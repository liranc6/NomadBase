# Internal Coordination: CSV Upload Map Fix

ORCH > ACK | req: CSV upload venues not reaching map.
XAA > r/o | address-only geocode is brittle; need name+address fallback for imported rows.
XPM > decision | keep UX unchanged; fix import/write path so markers appear on Explore.
PLAN > scope | `app.py`, traceability docs, validation.
SPDP > WIP | patch resolver fallback, then verify imported rows render.
XQA > note | confirm CSV import still accepts current headers and map shows markers.
SPDP > DONE | resolver fallback + CSV import validated in Python check.
