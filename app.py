"""TidePool Explorer: dependency-free Python development server."""
import json
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen, Request
from concurrent.futures import ThreadPoolExecutor
from coastal_sites import coastal_sites
from data_sources import load_catalogue, assign_station, station_site, coordinate_site, wildlife
from tide_curve import with_fallback_curve

ROOT = Path(__file__).resolve().parent
SITES = [
    dict(id='fitzgerald', name='Fitzgerald Marine Reserve', lat=37.524, lng=-122.516, station='9414290', station_name='San Francisco', source='https://www.smcgov.org/parks/fitzgerald-marine-reserve'),
    dict(id='bridges', name='Natural Bridges State Beach', lat=36.951, lng=-122.058, station='9413450', station_name='Monterey', source='https://www.parks.ca.gov/?page_id=541'),
    dict(id='lobos', name='Point Lobos State Natural Reserve', lat=36.516, lng=-121.942, station='9413450', station_name='Monterey', source='https://www.parks.ca.gov/?page_id=571'),
    dict(id='cabrillo', name='Cabrillo National Monument', lat=32.669, lng=-117.244, station='9410170', station_name='San Diego', source='https://www.nps.gov/cabr/planyourvisit/tidepools.htm'),
]
for site in SITES:
    site.update(country='United States', region='California', timezone='America/Los_Angeles', habitat='pacific')
SITES += [
    dict(id='yaquina', name='Yaquina Head · Cobble Beach', lat=44.675, lng=-124.079, station='9435380', station_name='South Beach', country='United States', region='Oregon', timezone='America/Los_Angeles', habitat='pacific', source='https://www.blm.gov/visit/yaquina-head-outstanding-natural-area'),
    dict(id='ruby', name='Ruby Beach · Olympic National Park', lat=47.710, lng=-124.416, station='9442396', station_name='La Push', country='United States', region='Washington', timezone='America/Los_Angeles', habitat='pacific', source='https://www.nps.gov/olym/planyourvisit/tidepool-activities.htm'),
    dict(id='wonderland', name='Wonderland · Acadia National Park', lat=44.229, lng=-68.321, station='8413320', station_name='Bar Harbor', country='United States', region='Maine', timezone='America/New_York', habitat='atlantic', source='https://www.nps.gov/thingstodo/tidepooling-wonderland.htm'),
    dict(id='schoodic', name='Schoodic Peninsula · Acadia', lat=44.334, lng=-68.060, station='8413320', station_name='Bar Harbor', country='United States', region='Maine', timezone='America/New_York', habitat='atlantic', source='https://www.nps.gov/acad/planyourvisit/tidepooling.htm'),
]
SITES += coastal_sites()
for site in SITES:
    site.setdefault('kind', 'Tidepool shore')
CATALOGUE = load_catalogue()
US_REGIONS = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR VI GU AS MP UM'.split())
STATIONS = [station for station in CATALOGUE['stations'] if station.get('state') in US_REGIONS]
SITES = [assign_station(site, STATIONS) for site in SITES]
SITE_INDEX = {site['id']: site for site in SITES}
STATION_INDEX = {'noaa-' + station['id']: station_site(station) for station in STATIONS}

def find_site(site_id):
    if site_id.startswith('coordinates:'):
        try:
            _, lat, lng = site_id.split(':')
            return coordinate_site(lat,lng,STATIONS)
        except (ValueError, TypeError):
            return None
    return SITE_INDEX.get(site_id) or STATION_INDEX.get(site_id)
SPECIES = [
    dict(name='California mussel', sci='Mytilus californianus', zone='high', desc='Look for dense beds on exposed rocky surfaces.'),
    dict(name='Aggregating anemone', sci='Anthopleura elegantissima', zone='mid', desc='Look in shallow pools and moist crevices; exposed animals may be closed.'),
    dict(name='Ochre sea star', sci='Pisaster ochraceus', zone='mid', desc='Look along shaded rock faces and beneath ledges without moving rocks.'),
    dict(name='Purple sea urchin', sci='Strongylocentrotus purpuratus', zone='low', desc='Look for purple spines in submerged rock depressions.'),
    dict(name='Giant green anemone', sci='Anthopleura xanthogrammica', zone='low', desc='Look in deeper rocky pools and channels from a distance.'),
]
for animal in SPECIES:
    animal['habitat'] = 'pacific'
SPECIES += [
    dict(name='Common periwinkle', sci='Littorina littorea', zone='high', habitat='atlantic', desc='Look for small grazing snails on rocky shores.'),
    dict(name='Blue mussel', sci='Mytilus edulis', zone='mid', habitat='atlantic', desc='Look for clustered shells attached to rocks.'),
    dict(name='Green sea urchin', sci='Strongylocentrotus droebachiensis', zone='low', habitat='atlantic', desc='Look in submerged rocky habitat; observe without handling.'),
]
CACHE = {}
PHOTO_FILE = ROOT / 'species_photos.json'
if PHOTO_FILE.exists():
    photos = json.loads(PHOTO_FILE.read_text(encoding='utf-8'))
    for animal in SPECIES:
        animal['photo'] = photos.get(animal['sci'])

def fetch(params):
    key = urlencode(params)
    if key in CACHE and time.monotonic() - CACHE[key][0] < 900:
        return CACHE[key][1]
    request = Request('https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?' + key,
                      headers={'User-Agent': 'TidePoolExplorer-hackathon/1.0'})
    with urlopen(request, timeout=15) as response:
        result = json.load(response)
    if 'error' in result or not result.get('predictions'):
        raise ValueError('NOAA returned no predictions for this station/date.')
    CACHE[key] = (time.monotonic(), result['predictions'])
    return result['predictions']

def iso(value):
    return datetime.strptime(value, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc).isoformat()

def forecast(site, date):
    start = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    if abs((start.date() - datetime.now(timezone.utc).date()).days) > 365:
        raise ValueError('Choose a date within one year of today.')
    if not site['station']:
        return with_fallback_curve(dict(site=site, available=False, curve=[], lows=[], events=[], message='No nearby US NOAA tide reference is available for these coordinates. Choose a listed US destination or station.'))
    params = dict(product='predictions', application='TidePoolExplorer', station=site['station'],
                  begin_date=(start - timedelta(days=1)).strftime('%Y%m%d'), end_date=(start + timedelta(days=2)).strftime('%Y%m%d'),
                  datum='MLLW', time_zone='gmt', units='english', format='json')
    with ThreadPoolExecutor(max_workers=2) as pool:
        curve_future = pool.submit(fetch, dict(params, interval='h')) if site.get('station_type') != 'S' else None
        lows_future = pool.submit(fetch, dict(params, interval='hilo'))
        events = [dict(time=iso(p['t']), height=float(p['v']), type=p['type']) for p in lows_future.result()]
        curve = []
        if curve_future:
            try:
                curve = [dict(time=iso(p['t']), height=float(p['v'])) for p in curve_future.result()]
            except Exception:
                pass  # Preserve a valid high/low table if hourly predictions are unsupported.
        lows = [p for p in events if p['type'] == 'L']
    return with_fallback_curve(dict(site=site, curve=curve, lows=lows, events=events, source='NOAA CO-OPS predictions',
                chart_note='' if curve else 'This station provides high/low events only. See the tide table; no hourly curve is generated.',
                datum='MLLW', units='feet', fetched_at=datetime.now(timezone.utc).isoformat()))

class Handler(BaseHTTPRequestHandler):
    def send(self, status, payload, content_type='application/json; charset=utf-8'):
        data = json.dumps(payload).encode() if not isinstance(payload, bytes) else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path.startswith('/assets/'):
            # Only serve flat, checked-in image filenames, never arbitrary paths.
            filename = url.path.removeprefix('/assets/')
            if '/' in filename or '\\' in filename or '..' in filename or not filename.endswith('.jpg'):
                return self.send(404, dict(error='Not found'))
            path = ROOT / 'assets' / filename
            if not path.is_file():
                return self.send(404, dict(error='Not found'))
            return self.send(200, path.read_bytes(), 'image/jpeg')
        if url.path in ('/', '/index.html', '/explorer.js', '/theme.css', '/sea-friends.svg'):
            filename = url.path.lstrip('/') or 'index.html'
            content_type = 'image/svg+xml' if filename.endswith('.svg') else 'text/css' if filename.endswith('.css') else 'text/javascript' if filename.endswith('.js') else 'text/html'
            return self.send(200, (ROOT / filename).read_bytes(), content_type + '; charset=utf-8')
        if url.path == '/api/sites':
            return self.send(200, dict(sites=SITES, species=SPECIES, station_count=len(STATIONS), catalogue_updated_at=CATALOGUE['fetched_at']))
        if url.path == '/api/location':
            try:
                return self.send(200, coordinate_site(query.get('lat',[''])[0],query.get('lng',[''])[0],STATIONS))
            except ValueError:
                return self.send(400, dict(error='Enter valid latitude and longitude values.'))
        if url.path == '/api/stations':
            search = query.get('q', [''])[0].strip().lower()[:100]
            try:
                offset = max(0, int(query.get('offset', ['0'])[0]))
            except ValueError:
                return self.send(400, dict(error='Invalid station page.'))
            matches = [s for s in STATION_INDEX.values() if all(word in (s['name']+' '+s['region']+' '+s['station']).lower() for word in search.split())]
            return self.send(200, dict(stations=matches[offset:offset+30], total=len(matches), offset=offset, catalogue_updated_at=CATALOGUE['fetched_at']))
        if url.path == '/api/wildlife':
            site = find_site(query.get('site', [''])[0])
            if site is None:
                return self.send(400, dict(error='Choose a destination or NOAA station.'))
            try:
                return self.send(200, wildlife(site))
            except Exception:
                return self.send(502, dict(error='Nearby observation data is unavailable. Try again later or view the regional guide.'))
        if url.path == '/api/tides':
            site = find_site(query.get('site', [''])[0])
            if site is None:
                return self.send(400, dict(error='Choose a supported tidepool site.'))
            try:
                return self.send(200, forecast(site, query.get('date', [datetime.now(timezone.utc).date().isoformat()])[0]))
            except ValueError as error:
                return self.send(400, dict(error=str(error)))
            except Exception:
                return self.send(502, dict(error='The tide provider is unavailable for this station/date. Try again shortly; no simulated predictions are shown.'))
        return self.send(404, dict(error='Not found'))

if __name__ == '__main__':
    print('TidePool Explorer: http://127.0.0.1:8000', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
