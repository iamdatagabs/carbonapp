# Frontend and API

## Run locally

Install the API extra and development tools:

```bash
pip install -e ".[api,dev]"
uvicorn carbonapp.api:create_app --factory --reload
```

The API reads `data/raw/[quad]base_nirs_refletancia.csv` by default. Set `CARBONAPP_DATA_PATH` to override it.

Open `apps/frontend/index.html` through a static HTTP server. If the frontend is served from another origin, define `window.CARBONAPP_API_BASE` before loading `app.js` and configure CORS at the API deployment layer for the exact frontend origin. Do not use a wildcard origin with credentials.

## Endpoints

- `GET /health`
- `GET /api/v1/metadata/depths`
- `GET /api/v1/dataset/summary?target=TOC|N`
- `GET /api/v1/profiles/{point_id}?target=TOC|N`
- `GET /api/v1/profiles-3d?target=TOC|N`

The 3D view uses a categorical sampling-point index and real depth midpoints/intervals. It is not geographic interpolation. Profile summaries weight each point equally after collapsing repeated rows within each `Sample Number`.

## Deployment boundary

The frontend is static and can be hosted on GitHub Pages or any static host. The API requires a Python ASGI host and access to the validated CSV. Configure CORS, dataset path, health checks, and persistent/versioned data storage before public deployment. This branch does not automatically publish or deploy either service.
