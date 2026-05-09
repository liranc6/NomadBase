# Internal Coordination: OpenStreetMap + Nominatim App Update

ORCH > ACK | req: make OSM + Nominatim explicit in app geocoding.
XAA > r/o | free stack already fits the app; just formalize the provider choice.
XPM > decision | keep the public UX unchanged; clarify and harden the geocoder path.
PLAN > scope | `app.py`, `README.md`, traceability docs.
SPDP > WIP | point geocoder config at OpenStreetMap/Nominatim directly.
XQA > note | verify app still resolves and maps imported venues.
SPDP > DONE | geocoder now targets `nominatim.openstreetmap.org`; README updated.
