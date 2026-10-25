"""Resolve standard IUCN categories from GBIF and iNaturalist."""
import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from conservation import LABELS, status_for

CACHE={}
GBIF_CODES={'LEAST_CONCERN':'LC','NEAR_THREATENED':'NT','VULNERABLE':'VU','ENDANGERED':'EN','CRITICALLY_ENDANGERED':'CR','EXTINCT_IN_THE_WILD':'EW','EXTINCT':'EX','DATA_DEFICIENT':'DD','NOT_EVALUATED':'NE'}

def request_json(url,body=None):
    request=Request(url,data=json.dumps(body).encode() if body is not None else None,
                    headers={'User-Agent':'TidePoolExplorer/1.0 educational prototype','Accept':'application/json','Content-Type':'application/json'})
    with urlopen(request,timeout=8) as response:
        return json.load(response)

def gbif_assessment(name):
    match=request_json('https://api.gbif.org/v1/species/match?'+urlencode(dict(name=name,strict='true')))
    if match.get('matchType')!='EXACT' or match.get('rank')!='SPECIES':
        return None
    key=match.get('acceptedUsageKey') or match.get('usageKey')
    if not key:
        return None
    record=request_json(f'https://api.gbif.org/v1/species/{key}/iucnRedListCategory')
    code=record.get('code') or GBIF_CODES.get(record.get('category'))
    if code not in LABELS:
        return None
    return dict(code=code,label=LABELS[code],source='IUCN category via GBIF',scope='Global assessment' if code!='NE' else 'Global category · no assessment in GBIF',equivalent=False,
                source_url=f'https://www.gbif.org/species/{key}',matched_name=match.get('scientificName'),provider_details=record)

def resolve_status(name,taxon=None):
    cached=CACHE.get(name)
    if cached and time.monotonic()-cached[0]<(300 if cached[1]['failed'] else 86400):
        extra=cached[1]
    else:
        evidence=[];failed=[]
        for provider_name,provider in (('GBIF',gbif_assessment),):
            try:
                record=provider(name)
                if record:evidence.append(record)
            except Exception:
                failed.append(provider_name)
        extra=dict(evidence=evidence,failed=failed)
        if len(CACHE)>256:CACHE.clear()
        CACHE[name]=(time.monotonic(),extra)
    original=status_for(taxon or {})
    evidence=list(extra['evidence'])
    if original['code']!='UNKNOWN' and not original.get('equivalent'):evidence.append(original)
    def priority(record):
        if record['source']=='IUCN category via GBIF' and record['code']!='NE':return 0
        if record['code']!='NE' and record['scope']=='Global assessment' and 'iucn' in record['source'].lower():return 1
        if record['source']=='IUCN category via GBIF' and record['code']=='NE':return 3
        if record['code']!='NE':return 4
        return 5
    if evidence:
        result=dict(sorted(evidence,key=priority)[0])
    else:
        code='UNKNOWN' if extra['failed'] else 'UNASSESSED'
        result=dict(code=code,label='Status temporarily unavailable' if extra['failed'] else 'No published assessment found',source='GBIF and iNaturalist',scope='Assessment coverage',equivalent=False,source_url='https://www.gbif.org')
    result['assessments']=evidence
    result['checked_sources']=['GBIF / IUCN categories','iNaturalist']
    result['unavailable_sources']=extra['failed']
    return result
