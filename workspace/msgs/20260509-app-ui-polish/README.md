# Internal Coordination: NomadBase UI Polish

## Thread
ORCH > ACK | req: UI polish for NomadBase.
ORCH > INVOKE | XAA | XPM | XAD.
XAA > r/o | issue: flat visual hierarchy | public view still reads dev-tool-ish.
XAA > SITREP | no new feature needed => polish shell, tighten spacing, sharpen Explore entry point.
XPM > decision frame | public UX should feel shareable first | admin/setup stays hidden unless needed.
XAD > note | add stronger top-level hierarchy, compact status line, cleaner Explore layout, less visual noise.
PLAN > scope | app.py only | no deps | preserve Sheets flow + tabs.
ORCH > DECISION | ship compact hero/status, sidebar-driven Explore filters, card-like map/results layout.
SPDP > WIP | implement UI polish in app.py after this thread is written.
XQA > note | verify no layout regressions and no change to data flow.
SPDP > DONE | hero/status added | Explore filters moved to sidebar | map/results space cleaned up.
XQA > ACK | syntax clean | no data-flow changes observed.
