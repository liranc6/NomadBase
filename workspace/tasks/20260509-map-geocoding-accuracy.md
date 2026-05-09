# Tasks: Map Geocoding Accuracy

**Status**: IN PROGRESS
**Owner**: ORCH → SPDP

## Work Items
- WIP | make geocoding address-first for new and imported rows
- WIP | normalize noisy address strings before lookup
- WIP | batch coordinate writes back to Google Sheets
- WIP | confirm Explore map renders only valid coordinates

## CONSULT-LOG
- XAA | identified free-text geocoding + rate limits as the likely failure mode.
- XPM | approved a smaller fix: better geocoding inputs instead of changing map UX.
- SPDP | patched `app.py` and added sheet-write batching.

## STATUS
IN PROGRESS
