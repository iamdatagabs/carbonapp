# CarbonApp product architecture and MVP roadmap

## Product direction
Evolve from a research dashboard into a field-to-laboratory soil spectroscopy platform. Initial release is a research/field-data management tool, **not** a validated soil-diagnostic or decision-support system. Predictions must remain distinct from laboratory reference measurements.

## Recommended stack
| Layer | Technology | Responsibility |
|---|---|---|
| Web | Existing responsive HTML/CSS/JavaScript + Plotly | Research dashboard, project/sample administration |
| Backend | Java 21 + Spring Boot 3.x | REST API, domain rules, auth, audit and persistence |
| Database | PostgreSQL | Projects, points, depth intervals, field records and model-run metadata |
| Android | Kotlin + Jetpack Compose | Field capture, offline drafts and later synchronization |
| Scientific engine | Existing Python package | Spectral QC, preprocessing, training, validation and inference |
| Deployment | Docker; managed PostgreSQL; separate web/API/science services | Reproducible environments |

Start as a modular Spring Boot monolith, not microservices. Python remains the source of truth for scientific computation; Java orchestrates workflows and exposes stable API contracts.

## Initial domain model
- Project: campaign, protocol, owner and dates.
- SamplingPoint: project, point code and optional coordinates (never inferred).
- Sample: physical sample identifier, point, depth, collection time and chain-of-custody metadata.
- FieldRecord: field observations, notes and attachment references.
- LaboratoryResult: analyte, value, unit, method, laboratory and report date.
- Spectrum: instrument, scan identifier, wavelength/value pairs, calibration and QC status.
- ModelRun: model/version, dataset hash, training protocol and validation summary.
- Prediction: target, estimate, uncertainty interval, model run and status.

Do not treat historical `Sample Number` as a confirmed physical sample ID until its laboratory meaning is documented. Store provenance and units explicitly.

## MVP 0
- Spring Boot API: health, depth metadata and PostgreSQL field-record capture.
- Android Compose capture screen with local-draft state.
- Existing web dashboard remains the research visualization client.
- OpenAPI contract and Docker Compose for API + PostgreSQL.
- No production auth, multi-tenancy or scientific claims yet.

## MVP 1
Project/point management, sample registration, QR labels, immutable spectrum uploads, lab results with units/method, Python analysis jobs and versioned model runs.

## MVP 2
Room-backed offline Android capture, idempotent sync queue, QR scanning, optional GPS with explicit consent, instrument integration after hardware protocol is known, audit trail and role-based access.

## API v1
- `GET /api/v1/health`
- `GET /api/v1/metadata/depths`
- `GET /api/v1/field-records`
- `POST /api/v1/field-records`

## Product boundary
The historical dataset has no geographic coordinates; TOC units/reference method need confirmation; N remains exploratory. Label historical values as research data with incomplete provenance. Never present model estimates as laboratory results.
