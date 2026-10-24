"""Public data adapters. Tide gauges are not verified tidepool destinations."""
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CACHE = {}

def get_json(url, ttl=900):
    cached = CACHE.get(url)
    if cached and time.monotonic() - cached[0] < ttl:
        return cached[1]
    request = Request(url, headers={'User-Agent': 'TidePoolExplorer/1.0 educational-prototype'})
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    if len(CACHE) > 256:
        CACHE.clear()
    CACHE[url] = (time.monotonic(), result)
    return result

def distance(a, b):
    lat1, lat2 = math.radians(a['lat']), math.radians(b['lat'])
    x = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(math.radians(b['lng']-a['lng'])/2)**2
    return 6371 * 2 * math.asin(math.sqrt(min(1, x)))

def load_catalogue():
    path = ROOT / 'noaa_stations.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(stations=[], fetched_at=None)

def station_site(station):
    return dict(id='noaa-' + station['id'], name=station['name'], lat=station['lat'], lng=station['lng'],
                country='NOAA station catalogue', region=station.get('state') or 'Other NOAA coverage', timezone='UTC',
                habitat='unlisted', kind='Tide prediction station · not a verified tidepool',
                station=station['id'], station_name=station['name'], station_type=station['type'],
                station_distance_km=0, source='https://tidesandcurrents.noaa.gov/noaatidepredictions.html?id=' + station['id'])

def assign_station(site, stations):
    result = dict(site)
    if not stations or site['country'] != 'United States':
        return result
    assigned = next((s for s in stations if s['id'] == site.get('station')), None)
    nearest = assigned or min(stations, key=lambda station: distance(site, station))
    km = distance(site, nearest)
    if assigned or km <= 75:
        result.update(station=nearest['id'], station_name=nearest['name'], station_type=nearest['type'],
                      station_distance_km=round(km, 1), station_assignment='existing regional proxy' if assigned else 'nearest NOAA station by straight-line distance')
    return result

def coordinate_site(lat, lng, stations):
    lat, lng = float(lat), float(lng)
    if not math.isfinite(lat) or not math.isfinite(lng) or abs(lat)>90 or abs(lng)>180:
        raise ValueError('Enter a valid latitude and longitude.')
    site = dict(id=f'coordinates:{lat}:{lng}', name=f'Coordinates {lat:.4f}, {lng:.4f}',lat=lat,lng=lng,
                country='Custom coordinates',region='Coordinates',timezone='UTC',habitat='unlisted',
                kind='Unverified location · not a confirmed tidepool',station=None,station_name=None,
                source=f'https://www.openstreetmap.org/?mlat={lat}&mlon={lng}')
    if stations:
        nearest=min(stations,key=lambda station:distance(site,station))
        km=distance(site,nearest)
        if km<=75:
            site.update(station=nearest['id'],station_name=nearest['name'],station_type=nearest['type'],station_distance_km=round(km,1))
    return site

def wildlife(site):
    taxa_path = ROOT / 'marine_taxa.json'
    if not taxa_path.exists():
        raise RuntimeError('Run python prepare_data.py to load marine taxon IDs.')
    taxa = json.loads(taxa_path.read_text(encoding='utf-8'))
    params = dict(lat=site['lat'], lng=site['lng'], radius=10, taxon_id=','.join(str(t) for t in taxa.values()),
                  quality_grade='research', photos='true', photo_license='cc0,cc-by,cc-by-sa',
                  captive='false', geoprivacy='open', per_page=100, order_by='observed_on', order='desc')
    data = get_json('https://api.inaturalist.org/v1/observations?' + urlencode(params), ttl=3600)
    animals = {}
    for observation in data.get('results', []):
        taxon = observation.get('taxon') or {}
        name = taxon.get('name')
        photo = next((p for p in observation.get('photos', []) if p.get('license_code') in {'cc0','cc-by','cc-by-sa'}), None)
        if not name or not photo:
            continue
        if name in animals:
            animals[name]['sample_count'] += 1
            continue
        url = photo['url'].replace('square.', 'medium.').replace('http:', 'https:')
        if not url.startswith(('https://inaturalist-open-data.s3.amazonaws.com/', 'https://static.inaturalist.org/')):
            continue
        animals[name] = dict(name=taxon.get('preferred_common_name') or name, sci=name, zone='unclassified',
                             nearby=True, observed_on=observation.get('observed_on'), sample_count=1,
                             desc='Recorded within 10 km in public iNaturalist observations. Not a prediction of what is in this pool.',
                             observation_url='https://www.inaturalist.org/observations/' + str(observation['id']),
                             photo=dict(url=url, attribution=photo.get('attribution') or 'iNaturalist contributor',
                                        license=photo['license_code'], source='https://www.inaturalist.org/photos/' + str(photo['id'])))
    return dict(species=list(animals.values())[:12], radius_km=10, sampled_observations=len(data.get('results', [])),
                total_matching_observations=data.get('total_results', 0),
                message='Recent research-grade, openly photographed records within 10 km. Marine-related groups can include freshwater and terrestrial relatives. Empty results mean no matching records, not absence of wildlife.',
                fetched_at=datetime.now(timezone.utc).isoformat())
