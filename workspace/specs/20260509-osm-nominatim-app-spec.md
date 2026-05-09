# Technical Spec: OpenStreetMap + Nominatim App Update

**Date**: 2026-05-09
**Scope**: Make the app explicitly use OpenStreetMap + Nominatim for venue geocoding

## Problem
The app already uses Nominatim, but the current implementation does not clearly express that the geocoding provider is OpenStreetMap-backed. The request is to make that dependency explicit and keep the free stack aligned with the app.

## Approach
- Configure `geopy.Nominatim` with the OpenStreetMap Nominatim domain directly.
- Keep request throttling and caching in place.
- Update the setup docs so the free geocoding choice is clear.

## Acceptance Criteria
- The app geocoder is clearly tied to OpenStreetMap/Nominatim.
- Existing log and CSV import flows still place venues on the map.
- README/setup text reflects the chosen free stack.
