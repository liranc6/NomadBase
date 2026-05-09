# Technical Spec: CSV Upload Map Fix

**Date**: 2026-05-09
**Scope**: Make CSV-imported venues appear on the in-app map reliably

## Problem
CSV uploads depend on geocoding to populate Latitude/Longitude. When address-only geocoding fails, imported venues are saved without coordinates and do not appear on the Explore map.

## Fix Strategy
- Expand coordinate resolution to try venue-name fallbacks when address-only geocoding fails.
- Keep the existing sheet schema and map rendering flow intact.
- Preserve the current CSV headers and upload UX.

## Acceptance Criteria
- Uploaded CSV rows can still be imported with the current template.
- Imported venues with usable name/address data appear on the map after refresh.
- The app continues to load without syntax errors.
