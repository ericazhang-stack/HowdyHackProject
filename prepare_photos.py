"""Fetch exact taxon photos with attribution from iNaturalist, once for local use."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import app

def get(url):
    with urlopen(Request(url, headers={'User-Agent':'TidePoolExplorer/1.0 (educational prototype)'}), timeout=25) as response:
        return response.read()

def photo(animal):
    name = animal['sci']
    results = json.loads(get('https://api.inaturalist.org/v1/taxa?' + urlencode(dict(q=name, rank='species', per_page=5))))['results']
    taxon = next(t for t in results if t['name'] == name)
    image = taxon['default_photo']
    if image.get('license_code') not in {'cc0','cc-by','cc-by-sa'}:
        observations = json.loads(get('https://api.inaturalist.org/v1/observations?' + urlencode(dict(taxon_id=taxon['id'], photos='true', photo_license='cc0,cc-by,cc-by-sa', per_page=10))))['results']
        image = next(p for observation in observations for p in observation['photos'] if p.get('license_code') in {'cc0','cc-by','cc-by-sa'})
    url = (image.get('medium_url') or image['url'].replace('square', 'medium')).replace('http:', 'https:')
    filename = name.lower().replace(' ', '-') + '.jpg'
    data = get(url)
    (app.ROOT / 'assets' / filename).write_bytes(data)
    return name, dict(url='/assets/' + filename, attribution=image['attribution'], source='https://www.inaturalist.org/photos/' + str(image['id']), license=image['license_code'])

if __name__ == '__main__':
    (app.ROOT / 'assets').mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        photos = dict(pool.map(photo, app.SPECIES))
    (app.ROOT / 'species_photos.json').write_text(json.dumps(photos, indent=2), encoding='utf-8')
    print('Saved', len(photos), 'licensed organism photos with attribution.')
