# TidePool Explorer

A Python beach-hackathon prototype with a cream-and-pastel-blue interface, sea-animal clipart, tide tables, and organism photographs. Use Python 3.10 or newer. NOAA and iNaturalist need no API key or pip dependencies. The app lists US destinations and US/US-territory NOAA stations only.

## Deploy on Vercel without PowerShell

1. Save this project in a GitHub repository. GitHub Desktop or GitHub's browser upload can do this without terminal commands. Include `api/`, the root Python modules, `assets/`, and the JSON data files, alongside the HTML/CSS/JavaScript and deployment configuration.
2. In the Vercel dashboard, choose **Add New → Project** and import that repository.
3. Set **Framework Preset** to **Other** and **Root Directory** to the folder containing `vercel.json` (the repository root if you uploaded this project directly). Keep any custom dashboard build/output overrides disabled: the included configuration sets **Build Command** to `python3 build_static.py` and **Output Directory** to `public`.
4. Click **Deploy**. Open the HTTPS URL Vercel returns. Your visitors can use the website without installing Python or running PowerShell, and your computer does not need to stay on.

No API keys or environment variables are needed for the current NOAA/iNaturalist features. Later GitHub commits trigger new deployments. If you already have a Vercel project, check those same root/preset settings and redeploy after committing these changes.

The static page, script, stylesheet, SVG clipart and local organism photos are copied into `public/` during the build and served by Vercel. Five native Python functions in `api/` reuse the existing backend for `/api/sites`, `/api/stations`, `/api/location`, `/api/tides`, and `/api/wildlife`. `.python-version` selects Python 3.12. No long-running local server is required on Vercel. Source code and metadata JSON files are excluded from the public build; the Python function bundle retains the metadata needed for lookups.

NOAA/iNaturalist caches are best-effort in-memory caches in each function instance, not shared persistent storage. Upstream timeouts/unavailability still produce the app's normal error states. Update source metadata locally and commit it to refresh the deployed catalogue; deployed functions do not write to the repository.

The static build and all five Python entrypoints were tested locally. A live Vercel deployment has not been verified because this workspace has no connected Vercel account. Runtime reference: [Vercel Python functions](https://vercel.com/docs/functions/runtimes/python/api-directory).

If Vercel reports that a `functions` pattern matches no Serverless Functions, use the current `vercel.json`: it omits that optional wildcard configuration and lets Vercel discover the explicit `handler` classes in `api/`. Make sure all five `api/*.py` files are committed in the repository connected to Vercel. Set Root Directory to the folder containing `api/`, `vercel.json` and `build_static.py`, **not** `public/` or `api/`. Leave Framework Preset as Other and remove any dashboard overrides pointing to another build/output folder. Deploy the latest commit rather than rebuilding an older deployment's source.

## Optional local preview

```powershell
python app.py
```

For a full local website without PowerShell, double-click **start_local.pyw** in this folder with Python installed. It starts the backend and opens http://127.0.0.1:8000 in your browser. If this app is already running on that port, it opens the existing site.

You can also open **index.html** directly: relative CSS/JavaScript links, embedded clipart symbols and bundled preview-data.js let the styled interface, destinations, map and regional photo guide load without a server. This file preview explicitly labels live tide and wildlife APIs as unavailable; an HTML file cannot execute the Python backend. Map tiles and external libraries still need internet access.

For terminal-based local development, the command above opens the same site at http://127.0.0.1:8000; stop it with Ctrl+C. Restart after Python or dataset changes and refresh after frontend changes. Refresh the direct-file dataset with `python prepare_preview.py` when changing destination/species data.

If Windows points to a broken Store alias:

```powershell
& "$env:LOCALAPPDATA/Python/bin/python.exe" app.py
```

Internet is needed for tide providers, live iNaturalist records/photos, map tiles, fonts and map/chart libraries. The regional guide photos and clipart are served locally. The standard-library server is intended for local development.

## Coverage

- **48 US destinations.**
- **At least two destinations in all 23 ocean-coastal US states**, including Alaska and Hawaii; California has four. This scope excludes Great Lakes-only states and US territories.
- **All 48 curated US destinations now have regional NOAA tide references.** Existing station mappings are retained; other sites use the nearest prediction station within 75 km by straight-line distance. The UI shows that distance. This is an automatic regional reference, not validation that the station's tide matches the destination across headlands, estuaries or islands.
- **US and US-territory stations in the downloaded NOAA prediction catalogue are searchable and paginated.** Select one to retrieve its table and nearby wildlife. Stations are separate from the 48 curated destinations and are not presented as confirmed tidepools. Availability varies by station and date.
- Natural tidepool shores, rocky shores, sandy beaches, reefs, estuaries and tidal marshes are separately labeled. Sandy and marshy states have coastal nature alternatives; these are not presented as confirmed rocky tidepools.
- Each destination has an approximate coordinate, state/country, IANA time zone and official visitor-information link. The state/country filter narrows the destination menu. My Location finds a listed destination within 150 km; location coordinates are not stored.
- Custom coordinates can use a US NOAA station reference within 75 km; otherwise tide data is unavailable.


The core destination data lives in app.py; expanded US entries live in coastal_sites.py. Sources are linked in each entry and in the map popup. Check visitor guidance for access routes and current closures. Approximate markers do not establish safe or legal access to the water.

## Organism field guide and artwork

Cards include a conservation-status badge with a filter for individual categories, threatened categories (VU/EN/CR), and unavailable status. Assessment authority and geographic scope appear on the card. Global IUCN assessments are preferred when available; regional rankings are explicitly labeled as IUCN-equivalent categories with their original rank and region. These equivalents do not assert a global IUCN assessment or US legal protection. Missing assessments stay **Status unavailable**, distinct from **Not evaluated** and **Data deficient**. Filters apply to the displayed sample, not every organism at a destination. Refresh regional guide assessments with `python prepare_statuses.py`, then refresh `python prepare_preview.py` and redeploy/restart. Nearby records fetch detailed taxon assessments in one batch and cache them for up to a day.

Photos display fully centered with `object-fit: contain` and embedded EXIF orientation respected by the browser. Rotate-left/right and reset controls fit the rotated image to its frame without clipping; rotation choices are saved locally per photo. This is metadata-based orientation and full-photo fitting, not AI detection of the organism's body or its upright direction. No original photo is modified. Automatic body detection/orientation would require an additional vision model and cannot reliably define upright for every marine organism.

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

The countdown works for provider and interpolated curves. Exact provider low-tide times take priority. If only a sampled curve exists, the app finds interior minima and labels their timing approximate; it never infers a low from an endpoint or across a data gap. When today's last low has passed, it counts toward the next available low in the loaded window, including the following day. It advances only to real loaded events, and shows no countdown for past visit dates or missing predictions.

Stations are regional proxies, not measurements inside a particular pool. If NOAA fails, the interface reports unavailable data and never generates fictional tides. Tide height alone does not establish safe access: check daylight, surf, park hours and closures. Observe wildlife in place and do not collect organisms or move rocks.

## Data sources and next steps

- [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/dev/): tide predictions; use hourly and hilo intervals.
- [NOAA station metadata](https://api.tidesandcurrents.noaa.gov/mdapi/prod/): verify station type, location and datum support before integrating additional destinations.
- [iNaturalist API](https://api.inaturalist.org/v1/docs/): live nearby organism records and openly licensed observation photos. Credits and source records appear on cards.
- [California Academy of Sciences](https://www.calacademy.org/community-science/californias-tidepools/tidepooling-101): tidepool planning guidance and initial destination references.
- Official state park, NPS, BLM, wildlife-agency and local-manager links accompany each directory entry.

Next steps: locally validate station-to-shore mappings, improve marine habitat filtering, integrate surf/daylight constraints, and use Flask or FastAPI for deployment beyond this local prototype.

## Refresh catalogue metadata

```powershell
python prepare_data.py
```

This refreshes noaa_stations.json (the complete metadata snapshot and fetch timestamp) and marine_taxa.json. Restart the server afterward. The browser reports the catalogue snapshot date. Data adapters are in data_sources.py; app.py exposes /api/stations, /api/location, /api/tides and /api/wildlife.

## Verification

```powershell
python -m unittest -v
```

Tests cover coastal-state coverage, photo credits, station selection, catalogue pagination, subordinate stations, partial hourly failures, wildlife sampling, frontend element references and API routes. Browser visual testing is not available in this environment.

Curve tests additionally verify exact extrema, bounded/monotonic segments, midnight coverage from adjacent days, missing-event gaps, estimation labels, and preservation of existing provider curves. The map disables tile wrapping and constrains panning to one world extent. The interface uses cream, lagoon, powder and periwinkle blues with clipart distributed along different section edges.

An optional live US public-source check:

```powershell
python verify_live.py
```

During development, NOAA returned tide tables at all **43 distinct station references serving the 48 curated US destinations**. iNaturalist returned 12 photographed taxa each in samples at Fitzgerald and Galveston. This does not verify every NOAA station, every date, exact pool conditions, or photo availability everywhere.
