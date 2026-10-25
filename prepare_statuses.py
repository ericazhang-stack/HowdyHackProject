"""Refresh sourced conservation records for the regional photo guide."""
import json
from datetime import datetime,timezone
from urllib.parse import urlencode
import app
from data_sources import get_json
from conservation import status_for

if __name__=='__main__':
    statuses={}
    for animal in app.SPECIES:
        matches=get_json('https://api.inaturalist.org/v1/taxa?'+urlencode(dict(q=animal['sci'],per_page=5)))
        taxon=next(t for t in matches['results'] if t['name']==animal['sci'])
        detail=get_json('https://api.inaturalist.org/v1/taxa/'+str(taxon['id']))['results'][0]
        result=status_for(detail)
        result['retrieved_at']=datetime.now(timezone.utc).isoformat()
        statuses[animal['sci']]=result
    (app.ROOT/'species_statuses.json').write_text(json.dumps(statuses,indent=2),encoding='utf-8')
    print('Saved sourced status metadata for',len(statuses),'organisms.')
    print('Categories:',{name:value['code'] for name,value in statuses.items()})
