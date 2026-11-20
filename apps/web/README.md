# CarbonApp Web — field capture MVP

Static, responsive web client for the Java product API. It creates and lists
field records through `/api/v1/field-records`.

Serve this folder with any static HTTP server. The default API is
`http://localhost:8080`; set `window.CARBONAPP_API_BASE` before loading
`app.js` to target another API origin.

This development prototype has no authentication. Do not expose it publicly or
enter personal/sensitive information until the backend security and audit
controls are implemented.
