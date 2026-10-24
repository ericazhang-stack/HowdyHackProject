import importlib
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import urlopen
import app
from build_static import build

class VercelTests(unittest.TestCase):
    def test_direct_file_preview_has_local_assets_and_destinations(self):
        import re
        html=(app.ROOT/'index.html').read_text(encoding='utf-8')
        local_assets=re.findall(r'(?:src|href)="(\./[^"]+)"',html)
        self.assertIn('./theme.css',local_assets)
        self.assertIn('./explorer.js',local_assets)
        self.assertIn('./preview-data.js',local_assets)
        for path in local_assets:
            self.assertTrue((app.ROOT/path).is_file(),path)
        text=(app.ROOT/'preview-data.js').read_text(encoding='utf-8')
        data=json.loads(text.split('window.TIDEPOOL_PREVIEW = ',1)[1].rstrip(';\n'))
        self.assertEqual(len(data['sites']),48)
        self.assertTrue(all(site['country']=='United States' for site in data['sites']))
        self.assertIn('id="sea-friend-symbols"',html)

    def test_public_build_contains_frontend_and_photos_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=build(Path(temporary)/'public')
            self.assertEqual((output/'index.html').read_bytes(),(app.ROOT/'index.html').read_bytes())
            for name in ['explorer.js','theme.css','sea-friends.svg']:
                self.assertTrue((output/name).is_file())
            self.assertEqual(len(list((output/'assets').glob('*.jpg'))),8)
            self.assertFalse(list(output.rglob('*.py')))
            self.assertFalse(list(output.rglob('*.json')))
            # Rebuilds must be repeatable without downloading metadata/photos.
            build(output)

    def test_each_vercel_entrypoint_serves_its_api_path(self):
        paths={
            'sites':'/api/sites',
            'stations':'/api/stations?q=Honolulu',
            'location':'/api/location?lat=37.5&lng=-122.5',
            'tides':'/api/tides?site=fitzgerald&date=2026-10-24',
            'wildlife':'/api/wildlife?site=fitzgerald',
        }
        with patch.object(app,'forecast',return_value=dict(source='NOAA',events=[])), patch.object(app,'wildlife',return_value=dict(species=[])):
            for name,path in paths.items():
                handler=importlib.import_module('api.'+name).handler
                server=ThreadingHTTPServer(('127.0.0.1',0),handler)
                threading.Thread(target=server.serve_forever,daemon=True).start()
                try:
                    with urlopen(f'http://127.0.0.1:{server.server_port}'+path) as response:
                        self.assertEqual(response.status,200)
                        self.assertIsInstance(json.load(response),dict)
                        self.assertEqual(response.headers['Cache-Control'],'no-store')
                finally:
                    server.shutdown()
                    server.server_close()

if __name__=='__main__':
    unittest.main()
