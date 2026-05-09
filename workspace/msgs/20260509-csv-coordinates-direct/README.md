# Internal Coordination: CSV Coordinates Direct

ORCH > ACK | req: trust CSV Latitude/Longitude directly.
XAA > r/o | coordinates already exist; geocoding should be fallback only.
XPM > decision | keep the upload UX unchanged and prefer supplied coordinates.
PLAN > scope | `app.py`, `README.md`, traceability docs.
SPDP > WIP | update importer to use CSV coordinates first.
XQA > note | verify uploaded rows map without lookup when coords exist.
SPDP > DONE | coordinate-first CSV import validated.
