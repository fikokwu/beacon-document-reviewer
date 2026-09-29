# Deployment Runbook

**Live URL:** <your-cloud-run-url>

| Setting | Value |
|---|---|
| GCP project | `<your-gcp-project>` (the same project as the Gemini key) |
| Service | Cloud Run `regenmed-reviewer`, region `northamerica-northeast2` (Toronto) |
| Image | Built by Cloud Build from the repo `Dockerfile`: Node builds the React app, then Python 3.12-slim serves the API and the page |
| Secret | `gemini-api-key` in Secret Manager → env `GEMINI_API_KEY` |
| Env vars | `GEMINI_MODEL=gemini-3.1-pro-preview`, `GEMINI_THINKING_LEVEL=low`, `GEMINI_TIMEOUT_S=150` |
| Resources | 1 vCPU, 1 GiB, request timeout 300 s, min 1 / max 3 instances, CPU boost |
| Access | Public (`--allow-unauthenticated`) |

## Redeploy (after merging to `main`)

```bash
gcloud auth login                     # the account that owns the project
gcloud config set project <your-gcp-project>
git checkout main && git pull
gcloud run deploy regenmed-reviewer --source . --region northamerica-northeast2 \
  --allow-unauthenticated --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars GEMINI_MODEL=gemini-3.1-pro-preview,GEMINI_THINKING_LEVEL=low,GEMINI_TIMEOUT_S=150 \
  --memory 1Gi --cpu 1 --timeout 300 --min-instances 1 --max-instances 3 --cpu-boost
```

## Smoke test

```bash
U=<your-cloud-run-url>
curl $U/api/health                                   # {"ok":true}
curl -F "file=@tests/fixtures/samples/24015 QS-F-049_12052024134037.PDF;type=application/pdf" $U/api/review
```

## Common tasks

| Task | Command |
|---|---|
| Rotate the Gemini key | `printf '%s' 'NEW_KEY' \| gcloud secrets versions add gemini-api-key --data-file=-`, then redeploy (or `gcloud run services update regenmed-reviewer --region northamerica-northeast2 --update-secrets GEMINI_API_KEY=gemini-api-key:latest`) |
| Switch model | `gcloud run services update regenmed-reviewer --region northamerica-northeast2 --update-env-vars GEMINI_MODEL=gemini-pro-latest` |
| View logs | `gcloud run services logs read regenmed-reviewer --region northamerica-northeast2 --limit 50` |
| Roll back | `gcloud run services update-traffic regenmed-reviewer --region northamerica-northeast2 --to-revisions REVISION=100` |
| Save money after the hackathon | `gcloud run services update regenmed-reviewer --region northamerica-northeast2 --min-instances 0` |

## One-time setup (already done, 2026-09-26)
1. Enabled APIs: Cloud Run, Cloud Build, Artifact Registry, Secret Manager.
2. Created secret `gemini-api-key` and granted `roles/secretmanager.secretAccessor` to `<project-number>-compute@developer.gserviceaccount.com`.
3. Granted `roles/run.builder` to the same service account. New projects need this for `--source` builds.
