# Internal Coordination: Map Geocoding Accuracy

ORCH > ACK | bug: blank coords + one wrong marker on Explore map.
XAA > r/o ambiguity | free-text Nominatim calls are rate-limited; venue name bias can outrank accurate addresses.
XPM > decision | prefer address-first geocoding, keep sheet-backed map, surface failures better.
PLAN > scope | `app.py`, traceability docs.
SPDP > WIP | patch geocoder normalization + write batching.
XQA > note | validate syntax and map path after patch.
SPDP > SITREP | root cause: startup path can fail on sheet backfill writes; make write-back best-effort.
