"""Dev tool: review one PDF from the command line and print the result as JSON.

Usage: python -m scripts.review_pdf "tests/fixtures/samples/25017 MP-F-023.PDF"
"""

import logging
import sys
from pathlib import Path

from app.pipeline import review_pdf


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    result = review_pdf(Path(sys.argv[1]).read_bytes())
    print(result.model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    main()
