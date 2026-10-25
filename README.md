# Tide and Seek

**Small pools. Whole new worlds.**

Tide and Seek is a beach-themed web app that helps people plan tidepool visits and discover coastal wildlife. It brings location information, low-tide predictions, nearby organism records, and conservation categories into one experience.

## The problem

Planning a tidepool visit means checking several places for destinations, tide tables, wildlife information, and conservation status. Tide and Seek brings that information together so visitors can spend less time searching and more time exploring responsibly.

## What we built

- **48 US coastal destinations**, with at least two in each of the 23 ocean-coastal states, an interactive map, and official visitor-information links.
- **A unified tide dashboard** with a chart, high/low table, lowest-tide summary, and countdown to the next predicted low.
- **An estimated-curve algorithm** for stations without hourly predictions. It smoothly connects provider high/low events and clearly labels the result as an estimate.
- **Nearby wildlife photo cards** with observation dates, photographer credits, and source links.
- **Conservation-status filters** using standard IUCN categories available through GBIF and iNaturalist, with explicit labels for missing assessments.
- **An ocean-inspired interface** with bubble-shaped photos, animated surf, playful sea animals, an ocean-depth gradient, and optional synthesized wave audio. Decorative animations respect reduced-motion preferences.

## How it works

The HTML/CSS/JavaScript frontend sends requests to a Python backend. The backend retrieves tide predictions, nearby observations, and conservation records, then returns data for the chart, countdown, map, and organism cards.

When hourly tide data is unavailable, a half-cosine interpolation connects alternating high and low events. It passes through the original turning points, stays between their heights, and uses adjacent-day events to cover midnight. It does not extrapolate beyond available events or bridge missing cycles. Provider curves are solid; estimated curves are dashed.

Nearby wildlife results come from research-grade iNaturalist observations within **10 km**, sampling up to 100 recent matching records and displaying up to 12 distinct taxa. These are historical observations, not guaranteed sightings.

## Tech stack and data

| Component | Technology / source |
| --- | --- |
| Backend | Python standard library; Vercel Python Functions |
| Frontend | HTML, CSS, JavaScript |
| Map and tide chart | Leaflet, OpenStreetMap, Chart.js |
| Tide predictions and station metadata | NOAA CO-OPS APIs |
| Wildlife observations and licensed photos | iNaturalist API |
| Conservation categories | GBIF Species API and iNaturalist |
| Ocean ambience | Web Audio API |

No API keys or third-party Python packages are required for the implemented integrations.

## Try it

**Live website:** [Open Tide and Seek](https://howdyhackproject.vercel.app/index.html) ? use the hosted app without running a local server.

**Locally:** With Python installed, double-click `start_local.pyw`. It opens the full website at **http://127.0.0.1:8000**. Alternatively, run `python app.py`.

**On Vercel:** Import the repository, select **Framework Preset: Other**, and use the folder containing `vercel.json` as the project root. The included configuration builds the frontend and exposes the Python APIs.

Opening `index.html` directly provides a visual preview; live tides and nearby wildlife require the Python backend or a deployed site. Internet access is required for live data and external libraries. Enable ocean audio with the header toggle.

## Important limitations

Tides use regional NOAA station references, not measurements inside individual pools. Wildlife records do not predict which animals are present today, and missing conservation data does not mean low risk. Destinations include clearly labeled shoreline alternatives where rocky tidepools are uncommon. Visitors should check official access rules, surf, and daylight before visiting.

## Validation

Run `python -m unittest -v` for automated checks covering API routes, destination coverage, tide interpolation, conservation handling, and deployment packaging. `python verify_live.py` optionally checks live public data sources.
