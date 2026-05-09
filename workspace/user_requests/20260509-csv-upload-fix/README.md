# User Request: CSV Upload Map Fix

**Date**: 2026-05-09
**Type**: Bug fix

## Request
CSV uploads are inserting rows, but venue markers are not appearing on the map because Latitude/Longitude are not being written reliably.

## Desired Outcome
Make uploaded venues show up on the Explore map even when the CSV only provides venue name and address.

## Notes
- User does not care about exposing Latitude/Longitude.
- The key UX requirement is map visibility after CSV import.
