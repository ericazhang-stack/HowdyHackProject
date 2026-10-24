# TidePool Explorer

A Python beach-hackathon prototype with a cream-and-pastel-blue interface, sea-animal clipart, tide tables, and organism photographs. Use Python 3.10 or newer. NOAA and iNaturalist need no API key or pip dependencies. Optional WorldTides global predictions require your own API key and credits.

## Run

```powershell
python app.py
```

Open http://127.0.0.1:8000. Opening index.html directly will not work. Stop with Ctrl+C. Restart the server after Python or dataset changes, and refresh the browser after frontend changes.

If Windows points to a broken Store alias:

```powershell
& "$env:LOCALAPPDATA/Python/bin/python.exe" app.py
```

Internet is needed for tide providers, live iNaturalist records/photos, map tiles, fonts and map/chart libraries. The regional guide photos and clipart are served locally. The standard-library server is intended for local development.

## Coverage

- **51 destinations: 48 US destinations and 3 international guides.**
- **At least two destinations in all 23 ocean-coastal US states**, including Alaska and Hawaii; California has four. This scope excludes Great Lakes-only states and US territories.
- **All 48 curated US destinations now have regional NOAA tide references.** Existing station mappings are retained; other sites use the nearest prediction station within 75 km by straight-line distance. The UI shows that distance. This is an automatic regional reference, not validation that the station's tide matches the destination across headlands, estuaries or islands.
- **All 3,502 stations in the downloaded NOAA prediction catalogue are searchable and paginated.** Select one to retrieve its table and nearby wildlife. Stations are separate from the 51 curated destinations and are not presented as confirmed tidepools. Availability varies by station and date.
- Natural tidepool shores, rocky shores, sandy beaches, reefs, estuaries and tidal marshes are separately labeled. Sandy and marshy states have coastal nature alternatives; these are not presented as confirmed rocky tidepools.
- Each destination has an approximate coordinate, state/country, IANA time zone and official visitor-information link. The state/country filter narrows the destination menu. My Location finds a listed destination within 150 km; location coordinates are not stored.
- International destinations: Wembury (UK), Long Reef (Australia), and Goat Island (New Zealand). All support live organism-photo queries. Their tide predictions use WorldTides when configured; otherwise the UI explains the missing connection.
- Explore arbitrary coordinates using **Explore coordinates**. A NOAA reference is used when one is within 75 km; otherwise WorldTides is available when configured. Coordinates are unverified locations, not confirmed tidepools, and display times in UTC.

The core destination data lives in app.py; expanded US entries live in coastal_sites.py. Sources are linked in each entry and in the map popup. Check visitor guidance for access routes and current closures. Approximate markers do not establish safe or legal access to the water.

## Organism field guide and artwork

Section 04 defaults to **Nearby records with photos** for every curated destination, NOAA station, or coordinate. It queries public, open-location, research-grade iNaturalist observations within 10 km, excludes captive observations, and selects CC0/CC BY/CC BY-SA images with credits and source links. It samples the most recent 100 matching observations and shows up to 12 distinct taxa, record dates, and counts within that sample. Results are cached for one hour.

Queries cover Mollusca, Cnidaria, Echinodermata and Decapoda. These are marine-related groups, not an exhaustive marine-species inventory; freshwater and terrestrial relatives may appear near coasts. Empty results or unavailable photos do not mean an area has no organisms. These are historical records, not a model predicting which animals are present now. No intertidal zone is invented for live observations.

**Regional habitat guide** retains the eight locally saved photo cards and zone filters for Pacific and northern Atlantic examples. Regional examples are labeled separately from nearby observations.

Photographs are saved in assets/. species_photos.json records each photo's creator attribution, CC0/CC BY/CC BY-SA license, and original iNaturalist photo page. Credits are displayed below every photo. Original smiling crab, fish, octopus, turtle and sea-star vector decorations are in sea-friends.svg; these are decorative clipart, not identification images. Decorations are hidden from screen readers and never receive clicks.

To refresh organism photographs (requires internet access):

```powershell
python prepare_photos.py
```

Restart the Python server after refreshing. The downloader uses exact scientific-name matches and openly licensed photos from the iNaturalist API. Keep photo credits and license information with any shared copy of the project.

## Tide behavior

NOAA high/low tables and available hourly curves use feet relative to MLLW. The curve, lowest tide, countdown and turning-point table share one tide section; chart dots match table events. Provider curves are solid. When an hourly curve is missing, a dashed, clearly labeled **estimated visual curve** joins consecutive high/low events. Table heights and times always remain the original provider predictions.

The fallback in tide_curve.py uses a half-cosine between alternating extrema, with zero slope at each turning point. It includes preceding/following days' predicted turning points (already fetched by NOAA requests) to cover local midnight. It passes exactly through extrema and stays between their heights. It does not fit historical observations, train a forecast model, extrapolate past available endpoints, or bridge missing/contradictory events or gaps longer than 18 hours. Gaps stay visible in the chart. Estimated values are not used for the field guide's current-height note.

If hourly requests fail but events succeed, the table and eligible interpolation remain usable. Missing event data produces no estimate. The selected day shows its lowest provider-predicted tide and countdown to its next future low. Past dates have no countdown. NOAA responses are cached for 15 minutes.

Curated destinations use their local IANA time zone, including daylight-saving changes. NOAA catalogue stations and custom coordinates explicitly display UTC; no time zone is guessed from a state abbreviation.

Stations are regional proxies, not measurements inside a particular pool. If NOAA fails, the interface reports unavailable data and never generates fictional tides. Tide height alone does not establish safe access: check daylight, surf, park hours and closures. Observe wildlife in place and do not collect organisms or move rocks.

## Data sources and next steps

- [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/dev/): tide predictions; use hourly and hilo intervals.
- [NOAA station metadata](https://api.tidesandcurrents.noaa.gov/mdapi/prod/): verify station type, location and datum support before integrating additional destinations.
- [iNaturalist API](https://api.inaturalist.org/v1/docs/): live nearby organism records and openly licensed observation photos. Credits and source records appear on cards.
- [WorldTides](https://www.worldtides.info/apidocs): optional global modeled tide heights and extremes. See connection instructions below.
- [California Academy of Sciences](https://www.calacademy.org/community-science/californias-tidepools/tidepooling-101): tidepool planning guidance and initial destination references.
- Official state park, NPS, BLM, wildlife-agency and local-manager links accompany each directory entry.

Next steps: locally validate station-to-shore mappings, improve marine habitat filtering, integrate surf/daylight constraints, and use Flask or FastAPI for deployment beyond this local prototype.

## Optional international/global tides

Register with WorldTides and get a key from its developer account. Configure it in the server terminal, never in frontend JavaScript or a tracked file:

```powershell
$env:WORLDTIDES_API_KEY = 'your-own-key'
python app.py
```

WorldTides calls consume account credits. The adapter only runs for locations without a NOAA reference, when explicitly selected/refreshed. It uses the provider's returned vertical datum (requested MSL), converts metres to feet, shows copyright attribution, and preserves the prediction point returned by the provider. MSL and MLLW are different datums; the app never labels global values as NOAA MLLW. Model coverage is provider-dependent, not a guarantee for every coordinate.

The adapter does not share or cache WorldTides predictions across users; review the provider's license before public deployment. The live global integration could not be tested without your key; normalization and datum behavior are covered with mocked responses. No paid account was created and no paid API was called during development.

## Refresh catalogue metadata

```powershell
python prepare_data.py
```

This refreshes noaa_stations.json (the complete metadata snapshot and fetch timestamp) and marine_taxa.json. Restart the server afterward. The browser reports the catalogue snapshot date. Data adapters are in data_sources.py; app.py exposes /api/stations, /api/location, /api/tides and /api/wildlife.

## Verification

```powershell
python -m unittest -v
```

Tests cover coastal-state coverage, photo credits, station selection, catalogue pagination, subordinate stations, partial hourly failures, global datum conversion, wildlife sampling, frontend element references and API routes. Browser visual testing is not available in this environment.

Curve tests additionally verify exact extrema, bounded/monotonic segments, midnight coverage from adjacent days, missing-event gaps, estimation labels, and preservation of existing provider curves. The map disables tile wrapping and constrains panning to one world extent. The interface uses cream, lagoon, powder and periwinkle blues with clipart distributed along different section edges.

An optional live public-source check (never calls WorldTides):

```powershell
python verify_live.py
```

During development, NOAA returned tide tables at all **43 distinct station references serving the 48 curated US destinations**. iNaturalist returned 12 photographed taxa each in samples at Fitzgerald, Galveston, Wembury, Long Reef and Goat Island. This does not verify every NOAA station, every date, exact pool conditions, or photo availability everywhere.
