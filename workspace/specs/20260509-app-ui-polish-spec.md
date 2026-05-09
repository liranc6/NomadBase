# Technical Spec: NomadBase UI Polish

**Date**: 2026-05-09
**Scope**: Improve the public-facing UI in `app.py` without changing app behavior or storage.
**Decision**: Make the public app feel shareable by sharpening hierarchy and Explore layout.

## Requirements
- Keep the existing tabs and Sheets-backed flow.
- Make the landing area more polished and easier to understand at a glance.
- Make Explore the visual center of the app.
- Reduce setup noise for public users.

## Implementation Notes
- Add a compact top-level hero/status section.
- Keep metrics visible, but present them more cleanly.
- Move Explore filters into a cleaner layout so map and results scan better.
- Keep admin/setup content behind admin mode.

## Acceptance Criteria
- Public users land on a cleaner, more intentional UI.
- Explore reads as a primary product surface.
- No change to data storage or core logging flow.
- App still runs without syntax errors.
