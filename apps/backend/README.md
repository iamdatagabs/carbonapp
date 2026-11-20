# CarbonApp API — MVP
Java 21 + Spring Boot REST API. First slice: health, depth metadata and PostgreSQL-backed field-record capture.

Run with PostgreSQL available:
```bash
mvn spring-boot:run
mvn test
```
Environment: `DATABASE_URL`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `PORT`.

Endpoints: `GET /api/v1/health`, `GET /api/v1/metadata/depths`, `GET /api/v1/field-records`, `POST /api/v1/field-records`.

Example:
```json
{"projectCode":"DEMO","pointCode":"P01","depthCode":"A","notes":"Coleta inicial"}
```
Development MVP only: authentication, authorization, schema migrations, rate limiting, audit policies and idempotent mobile sync remain pending. Do not expose publicly with real field data.
