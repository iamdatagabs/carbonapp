# CarbonApp Web — field capture MVP

Static, responsive web client for the Java product API. It creates and lists
field records through `/api/v1/field-records`.

## Run locally

1. Start the API and PostgreSQL from the repository root with
   `docker compose up --build`.
2. In a second terminal, run `python -m http.server 5500 --directory apps/web`.
3. Open `http://localhost:5500`.

The API default is `http://localhost:8080`. The backend CORS allowlist permits
localhost and 127.0.0.1 on port 5500 by default; configure
`CARBONAPP_CORS_ALLOWED_ORIGINS` in a later deployment-specific config before
using a different origin.

This development prototype has no authentication. Do not expose it publicly or
enter personal/sensitive information until backend security and audit controls
are implemented.
