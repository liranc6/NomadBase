# Technical Spec: Geocoding Alternatives Evaluation

**Date**: 2026-05-09
**Scope**: Recommend a free geocoding/map stack that improves venue placement reliability

## Problem
The current address-based lookup is not reliable enough for all imported venues. The app needs a free approach that can place most normal venue records on the map without adding paid infrastructure.

## Evaluation Criteria
- Free to use or has a genuinely usable free tier
- Reliable enough for normal venue-import usage
- Easy to integrate into Streamlit + Python
- Clear rate-limit and caching story
- Minimal operational complexity

## Shortlist
### OpenStreetMap + Nominatim
- Best fit for free usage.
- Open geodata and a well-known geocoder.
- Requires aggressive caching, rate limiting, and respectful usage.
- Best choice when the app stays small to moderate.

### Mapbox
- Strong developer experience and polished APIs.
- Has meaningful free tiers, but is not the cleanest "always-free" path.
- Better as a paid-growth option than a pure free-stack recommendation.

### HERE Technologies
- Potentially usable via developer/free tier depending on account setup.
- More complex to validate and may still introduce account/billing dependency.
- Lower confidence for a free-only requirement.

## Recommendation
Use OpenStreetMap + Nominatim as the primary free geocoder, with caching and strict request throttling. Keep the app logic flexible so the provider can be swapped later if usage grows.

## Acceptance Criteria
- Recommendation clearly favors a free-first option.
- Tradeoffs for Mapbox and HERE are documented.
- The result is actionable for future implementation work.
