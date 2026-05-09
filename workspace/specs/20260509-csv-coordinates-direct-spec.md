# Technical Spec: Trust CSV Coordinates Directly

**Date**: 2026-05-09
**Scope**: Make CSV uploads use provided Latitude/Longitude values before geocoding

## Problem
The current CSV importer geocodes every row, even when the CSV already includes Latitude and Longitude. That wastes requests and can override accurate coordinates.

## Approach
- Parse Latitude and Longitude from the CSV when present.
- If both values are valid numbers, write them directly to the sheet.
- If coordinates are missing or invalid, fall back to the existing geocoding path.
- Keep the map rendering and sheet schema unchanged.

## Acceptance Criteria
- CSV rows with coordinates are imported without geocoding.
- Rows without coordinates still geocode as before.
- Imported venues continue to appear on the map.
