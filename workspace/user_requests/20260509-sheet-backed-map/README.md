# User Request: Sheet-Backed In-App Map

request: redesign app so new spots render on a real in-app map

Q? use sheet data + geocoding instead of the static Google My Maps embed.
A: yes — add Latitude/Longitude support, geocode new rows, and render markers inside Streamlit.

Acceptance
- New log entries geocode into Latitude/Longitude.
- CSV imports can also populate map coordinates.
- Explore tab shows a real in-app folium map from sheet data.
- Existing filters and details table still work.
