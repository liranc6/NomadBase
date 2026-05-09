# User Request: Trust CSV Coordinates Directly

**Date**: 2026-05-09
**Type**: Implementation update

## Request
The CSV upload should use the Latitude and Longitude values provided in the file instead of trying to geocode every row.

## Goal
Make CSV import place venues on the map immediately when coordinates are already present.

## Constraint
- Free tools only.
- Preserve the current Streamlit + Google Sheets flow.
