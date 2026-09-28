"""Thin Gemini wrapper: page images + prompt + Pydantic schema -> validated model.

Gemini only transcribes; it never decides pass/fail (ADR-001).
"""

import copy
import logging
import time
from typing import Any, Protocol, TypeVar

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from app import config
from app.schemas.common import CELL_DESCRIPTION

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# Rarely-used fields the model may omit (they default sensibly). Keeping them out of
# "required" cuts output tokens a lot on tables with hundreds of cells (ADR-010).
OPTIONAL_FIELDS = {"struck_through", "tally_count", "page", "box_2d", "void_initials",
                   "void_date", "row_voided", "marked_na", "shaded"}


class GeminiError(RuntimeError):
    """A user-facing failure talking to the AI service."""


class JsonGenerator(Protocol):
    def generate_json(self, images: list[bytes], prompt: str, schema: type[T],
                      model: str | None = None) -> T: ...


def to_gemini_schema(model: type[BaseModel], request_boxes: bool | None = None) -> dict[str, Any]:
    """Pydantic JSON schema with $refs inlined and defaults/titles dropped. Every property
    except OPTIONAL_FIELDS is required, so the model can't silently omit a cell (which
    would default to 'blank' and cause a false flag). `box_2d` is left out entirely unless
    requested (ADR-010)."""
    boxes = config.GEMINI_REQUEST_BOXES if request_boxes is None else request_boxes
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, list):
            return [resolve(n) for n in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            name = node["$ref"].split("/")[-1]
            if name == "FieldValue":  # compact wire format: one string per cell (ADR-014)
                return {"type": "string",
                        "description": node.get("description") or CELL_DESCRIPTION}
            target = resolve(copy.deepcopy(defs[name]))
            extras = {k: v for k, v in node.items() if k not in ("$ref", "default", "title")}
            return {**target, **extras}
        out = {}
        for key, value in node.items():
            if key in ("default", "title"):
                continue
            if key == "properties":
                out[key] = {name: resolve(sub) for name, sub in value.items()
                            if boxes or name != "box_2d"}
            else:
                out[key] = resolve(value)
        if "properties" in out:
            out["required"] = [k for k in out["properties"] if k not in OPTIONAL_FIELDS]
        return out

    return resolve(schema)


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None,
                 timeout_s: float | None = None):
        api_key = api_key or config.GEMINI_API_KEY
        self.model = model or config.GEMINI_MODEL
        if not api_key:
            raise GeminiError("The AI service is not configured (GEMINI_API_KEY is missing).")
        if not self.model:
            raise GeminiError("The AI service is not configured (GEMINI_MODEL is missing).")
        timeout_ms = int((timeout_s or config.GEMINI_TIMEOUT_S) * 1000)
        self._client = genai.Client(api_key=api_key,
                                    http_options=types.HttpOptions(timeout=timeout_ms))

    def generate_json(self, images: list[bytes], prompt: str, schema: type[T],
                      model: str | None = None) -> T:
        model = model or self.model
        contents: list[Any] = [prompt]
        contents += [types.Part.from_bytes(data=img, mime_type="image/png") for img in images]
        cfg = types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_json_schema=to_gemini_schema(schema),
            thinking_config=(types.ThinkingConfig(thinking_level=config.GEMINI_THINKING_LEVEL)
                             if config.GEMINI_THINKING_LEVEL else None),
        )
        last_error: Exception | None = None
        for attempt in (1, 2):  # retry once on invalid JSON or a 5xx
            try:
                started = time.monotonic()
                resp = self._client.models.generate_content(
                    model=model, contents=contents, config=cfg)
                usage = resp.usage_metadata
                log.info("Gemini %s %s: %.1fs, in=%s out=%s thoughts=%s", model,
                         schema.__name__, time.monotonic() - started,
                         getattr(usage, "prompt_token_count", None),
                         getattr(usage, "candidates_token_count", None),
                         getattr(usage, "thoughts_token_count", None))
                return schema.model_validate_json(resp.text or "")
            except ValidationError as exc:
                log.warning("Gemini returned invalid JSON (attempt %d): %s", attempt, exc)
                last_error = exc
            except errors.ServerError as exc:
                log.warning("Gemini server error (attempt %d): %s", attempt, exc)
                last_error = exc
            except errors.ClientError as exc:
                fallback = config.GEMINI_FALLBACK_MODEL
                if exc.code == 429 and fallback and model != fallback:
                    log.warning("Rate-limited on %s; retrying on %s", model, fallback)
                    return self.generate_json(images, prompt, schema, model=fallback)
                if exc.code == 429:
                    raise GeminiError("The AI service is busy right now. Please try again in a "
                                      "minute.") from exc
                raise GeminiError(f"The AI service rejected the request: {exc.message}") from exc
            except httpx.TimeoutException as exc:
                raise GeminiError("The AI service took too long to respond. "
                                  "Please try again.") from exc
        if isinstance(last_error, errors.ServerError):
            raise GeminiError("The AI service is busy right now. Please try again in a minute.") \
                from last_error
        raise GeminiError("The AI service returned an unusable response. "
                          "Please try again.") from last_error
