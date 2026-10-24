import json
import re
from collections import Counter
import threading
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.request import urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
import app
import data_sources
import os
from html.parser import HTMLParser


class ForecastTests(unittest.TestCase):
    def test_tide_chart_and_table_share_a_valid_section(self):
        class Structure(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack=[]
                self.errors=[]
                self.tide_elements={}
            def handle_starttag(self, tag, attributes):
                attrs=dict(attributes)
                if attrs.get('id') in {'tideChart','tide-table-body'}:
                    self.tide_elements[attrs['id']]=any(name=='section' and 'tide-section' in parent.get('class','').split() for name,parent in self.stack)
                if tag not in {'meta','link','input','br','img','hr'}:
                    self.stack.append((tag,attrs))
            def handle_endtag(self,tag):
                if not self.stack or self.stack[-1][0]!=tag:
                    self.errors.append(tag)
                else:
                    self.stack.pop()
        parser=Structure()
        parser.feed((app.ROOT/'index.html').read_text(encoding='utf-8-sig'))
        self.assertEqual(parser.errors,[])
        self.assertEqual(parser.stack,[])
        self.assertEqual(parser.tide_elements,{'tideChart':True,'tide-table-body':True})

    def test_subordinate_curve_uses_turning_points_without_hourly_request(self):
        date=datetime.now(timezone.utc).date().isoformat()
        events=[dict(t=date+' 00:00',v='-1',type='L'),dict(t=date+' 06:00',v='4',type='H')]
        with patch.object(app,'fetch',return_value=events) as fetch:
            result=app.forecast(dict(app.SITES[0],station_type='S'),date)
        self.assertEqual(fetch.call_count,1)
        self.assertEqual(result['curve_kind'],'interpolated')
        self.assertEqual(result['curve'][0]['height'],-1)
        self.assertEqual(result['curve'][-1]['height'],4)
        self.assertEqual(len(result['events']),2)

    def test_coordinate_locations_are_validated_and_not_called_tidepools(self):
        for lat,lng in [('nan','0'),('91','0'),('0','181'),('bad','0')]:
            with self.assertRaises(ValueError):
                data_sources.coordinate_site(lat,lng,app.STATIONS)
        site=data_sources.coordinate_site(37.5,-122.5,app.STATIONS)
        self.assertTrue(site['station'])
        self.assertEqual(site['timezone'],'UTC')
        self.assertIn('not a confirmed tidepool',site['kind'])
        self.assertEqual(app.find_site(site['id'])['id'],site['id'])
        self.assertIsNone(app.find_site('coordinates:nan:0'))

    def test_wildlife_rejects_unlicensed_photos_and_empty_results(self):
        record=dict(id=1,taxon=dict(name='Test species'),photos=[dict(id=2,url='https://static.inaturalist.org/photos/2/square.jpg',license_code=None)])
        with patch.object(data_sources,'get_json',return_value=dict(results=[record],total_results=1)):
            result=data_sources.wildlife(app.SITES[0])
        self.assertEqual(result['species'],[])
        self.assertEqual(result['total_matching_observations'],1)

    def test_all_us_destinations_have_explicit_regional_station(self):
        for site in app.SITES:
            if site['country']=='United States':
                self.assertTrue(site['station'])
                self.assertIn(site['station_type'], {'R','H','S'})
                self.assertGreaterEqual(site['station_distance_km'], 0)

    def test_complete_station_catalogue_is_distinct_from_destinations(self):
        self.assertGreater(len(app.STATIONS), 3000)
        self.assertEqual(len(app.SITES), 51)
        self.assertEqual(len(app.STATION_INDEX), len(app.STATIONS))
        station = next(iter(app.STATION_INDEX.values()))
        self.assertEqual(app.find_site(station['id']), station)
        self.assertIn('not a verified tidepool', station['kind'])
        self.assertEqual(station['timezone'], 'UTC')

    def test_one_turning_point_is_not_enough_to_estimate_a_curve(self):
        site = dict(app.SITES[0], station_type='S')
        date = datetime.now(timezone.utc).date().isoformat()
        with patch.object(app, 'fetch', return_value=[dict(t=date+' 12:00', v='-0.5', type='L')]) as fetch:
            result = app.forecast(site, date)
            self.assertEqual(result['curve'], [])
            self.assertEqual(len(result['events']), 1)
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(fetch.call_args.args[0]['interval'], 'hilo')

    def test_hourly_failure_keeps_valid_tide_table(self):
        def fetch(params):
            if params['interval']=='h':
                raise ValueError('Hourly unsupported')
            return [dict(t='2026-10-24 12:00', v='-0.5', type='L')]
        with patch.object(app, 'fetch', side_effect=fetch):
            result=app.forecast(dict(app.SITES[0],station_type='R'),datetime.now(timezone.utc).date().isoformat())
        self.assertEqual(result['curve'], [])
        self.assertEqual(len(result['lows']), 1)

    def test_global_provider_does_not_label_msl_as_mllw(self):
        from io import BytesIO
        response=dict(status=200,responseDatum='MSL',copyright='WorldTides test attribution',heights=[dict(dt=1792843200,height=1)],extremes=[dict(dt=1792843200,height=-1,type='Low')])
        with patch.dict(os.environ,{'WORLDTIDES_API_KEY':'test-key'}), patch.object(data_sources,'urlopen',return_value=BytesIO(json.dumps(response).encode())):
            result=data_sources.worldtides(app.SITES[-1], '2026-10-24')
        self.assertEqual(result['datum'],'MSL')
        self.assertAlmostEqual(result['curve'][0]['height'],3.280839895)
        self.assertEqual(result['attribution'],'WorldTides test attribution')

    def test_nearby_wildlife_uses_licensed_observation_photos(self):
        record=dict(id=123, observed_on='2026-10-24', taxon=dict(name='Test species',preferred_common_name='Test organism'),photos=[dict(id=99,url='https://static.inaturalist.org/photos/99/square.jpg',license_code='cc-by',attribution='Test photographer CC BY')])
        with patch.object(data_sources,'get_json',return_value=dict(results=[record,record],total_results=2)):
            result=data_sources.wildlife(app.SITES[0])
        self.assertEqual(len(result['species']),1)
        self.assertEqual(result['species'][0]['sample_count'],2)
        self.assertEqual(result['species'][0]['zone'],'unclassified')
        self.assertIn('medium.jpg',result['species'][0]['photo']['url'])

    def test_every_ocean_coastal_state_has_two_destinations(self):
        expected = {'Alabama','Alaska','California','Connecticut','Delaware','Florida','Georgia','Hawaii','Louisiana','Maine','Maryland','Massachusetts','Mississippi','New Hampshire','New Jersey','New York','North Carolina','Oregon','Rhode Island','South Carolina','Texas','Virginia','Washington'}
        counts = Counter(s['region'] for s in app.SITES if s['country'] == 'United States')
        self.assertEqual(set(counts), expected)
        self.assertTrue(all(counts[state] >= 2 for state in expected))

    def test_photos_have_files_and_credits(self):
        for animal in app.SPECIES:
            photo = animal['photo']
            self.assertTrue(photo['attribution'])
            self.assertTrue(photo['license'])
            self.assertTrue((app.ROOT / photo['url'].lstrip('/')).is_file())
            self.assertTrue((app.ROOT / photo['url'].lstrip('/')).read_bytes().startswith(b'\xff\xd8'))

    def test_frontend_element_references(self):
        html = (app.ROOT / 'index.html').read_text(encoding='utf-8-sig')
        javascript = (app.ROOT / 'explorer.js').read_text(encoding='utf-8')
        ids = set(re.findall(r'id="([^"]+)"', html))
        refs = set(re.findall(r"el\('([^']+)'\)", javascript))
        self.assertEqual(refs - ids, set())

    def test_international_locations_do_not_use_noaa(self):
        date = datetime.now(timezone.utc).date().isoformat()
        international = [s for s in app.SITES if s['country'] != 'United States']
        self.assertEqual(len(international), 3)
        with patch.dict(os.environ, {}, clear=True), patch.object(app, 'fetch') as fetch:
            for site in international:
                result = app.forecast(site, date)
                self.assertFalse(result['available'])
                self.assertEqual(result['curve'], [])
                self.assertEqual(result['lows'], [])
            fetch.assert_not_called()

    def test_location_metadata_and_species_regions(self):
        self.assertEqual(len({s['id'] for s in app.SITES}), len(app.SITES))
        for site in app.SITES:
            self.assertTrue(site['source'].startswith('https://'))
            self.assertIn('/', site['timezone'])
            if site['habitat'] in {'pacific','atlantic'}:
                self.assertTrue(any(s['habitat'] == site['habitat'] for s in app.SPECIES))
        self.assertEqual(next(s for s in app.SITES if s['id'] == 'wonderland')['timezone'], 'America/New_York')

    def test_utc_and_low_events(self):
        date = datetime.now(timezone.utc).date().isoformat()
        def fake(params):
            self.assertEqual(params['datum'], 'MLLW')
            self.assertEqual(params['time_zone'], 'gmt')
            return [dict(t=date + ' 12:00', v='-0.4', type='L'),
                    dict(t=date + ' 18:00', v='3.1', type='H')]
        with patch.object(app, 'fetch', side_effect=fake):
            result = app.forecast(app.SITES[0], date)
        self.assertEqual(len(result['lows']), 1)
        self.assertEqual(result['lows'][0]['height'], -0.4)
        self.assertTrue(result['lows'][0]['time'].endswith('+00:00'))

    def test_invalid_date(self):
        for date in ['bad', '2026-02-30', '1900-01-01']:
            with self.assertRaises(ValueError):
                app.forecast(app.SITES[0], date)

    def test_routes_and_upstream_failure(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        root = 'http://127.0.0.1:' + str(server.server_port)
        try:
            with urlopen(root + '/api/sites') as response:
                self.assertEqual(len(json.load(response)['sites']), 51)
            with urlopen(root + '/api/stations?q=Honolulu') as response:
                self.assertGreater(json.load(response)['total'],0)
            with urlopen(root + '/api/stations?offset=30') as response:
                self.assertEqual(json.load(response)['offset'],30)
            with urlopen(root + '/api/location?lat=-33.74&lng=151.312') as response:
                self.assertEqual(json.load(response)['timezone'],'UTC')
            with urlopen(root + '/') as response:
                self.assertIn(b'/explorer.js', response.read())
            with urlopen(root + '/theme.css') as response:
                self.assertIn('text/css', response.headers['Content-Type'])
            with urlopen(root + '/sea-friends.svg') as response:
                self.assertIn('image/svg+xml', response.headers['Content-Type'])
            with urlopen(root + app.SPECIES[0]['photo']['url']) as response:
                self.assertIn('image/jpeg', response.headers['Content-Type'])
            with self.assertRaises(HTTPError) as invalid:
                urlopen(root + '/api/tides?site=unknown')
            self.assertEqual(invalid.exception.code, 400)
            invalid.exception.close()
            with patch.object(app, 'forecast', side_effect=TimeoutError):
                with self.assertRaises(HTTPError) as unavailable:
                    urlopen(root + '/api/tides?site=fitzgerald')
                self.assertEqual(unavailable.exception.code, 502)
                self.assertIn('no simulated', json.load(unavailable.exception)['error'])
                unavailable.exception.close()
        finally:
            server.shutdown()
            server.server_close()

if __name__ == '__main__':
    unittest.main()
