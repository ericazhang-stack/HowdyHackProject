"""Refresh the NOAA prediction-station directory and iNaturalist taxon IDs."""
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from data_sources import ROOT, get_json

def prepare():
    data = get_json('https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions')
    stations = [dict(id=s['id'], name=s['name'], state=s.get('state'), lat=float(s['lat']), lng=float(s['lng']), type=s.get('type', 'S')) for s in data['stations']]
    (ROOT / 'noaa_stations.json').write_text(json.dumps(dict(fetched_at=datetime.now(timezone.utc).isoformat(), stations=stations)), encoding='utf-8')
    taxa = {}
    for name in ['Mollusca', 'Cnidaria', 'Echinodermata', 'Decapoda']:
        data = get_json('https://api.inaturalist.org/v1/taxa?' + urlencode(dict(q=name, per_page=10)))
        taxa[name] = next(t['id'] for t in data['results'] if t['name'] == name)
    (ROOT / 'marine_taxa.json').write_text(json.dumps(taxa, indent=2), encoding='utf-8')
    print('Saved', len(stations), 'NOAA prediction stations and', len(taxa), 'marine-related taxon groups.')

if __name__ == '__main__':
    prepare()
