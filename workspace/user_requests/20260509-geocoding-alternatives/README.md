# User Request: Geocoding Alternatives for Map Placement

**Date**: 2026-05-09
**Type**: Evaluation / architecture decision

## Request
The current address-to-map lookup is not reliable enough. Evaluate free alternatives for placing venues on the map and recommend the best option for NomadBase.

## Constraints
- Use only free tools or free tiers.
- Prefer an approach that keeps map placement reliable for normal app usage.
- Keep the recommendation practical for a Streamlit + Google Sheets app.

## Candidate Options
- OpenStreetMap + Nominatim
- Mapbox
- HERE Technologies
- Other free geocoding/map services if they fit better
