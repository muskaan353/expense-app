# AI Usage Log

## Tool

OpenAI Codex was used to inspect the assignment, scaffold the backend, implement
features, and run verification.

## Key prompt

Build a production-grade Django 5 and DRF backend for an AI-powered smart
expense sharing system with JWT, PostgreSQL, clean app boundaries, migrations,
OpenAPI documentation, and meaningful commit checkpoints.

## Reviewed AI mistakes

1. The generated `startapp` command initially targeted directories that did not
   exist. The directories were created explicitly before rerunning it.
2. The first PDF extraction attempt used a missing `pdftotext` binary. It was
   replaced with the available `pypdf` library.
3. PDF text output initially failed on the rupee symbol under the Windows
   console encoding. UTF-8 output was configured before retrying.
