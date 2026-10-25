"""Normalize reported conservation assessments without assuming missing = safe."""
LABELS={'LC':'Least concern','NT':'Near threatened','VU':'Vulnerable','EN':'Endangered','CR':'Critically endangered','EW':'Extinct in the wild','EX':'Extinct','DD':'Data deficient','NE':'Not evaluated','UNKNOWN':'Status unavailable'}
IUCN_CODES={0:'NE',5:'DD',10:'LC',20:'NT',30:'VU',40:'EN',50:'CR',60:'EW',70:'EX'}

def status_for(taxon):
    records=list(taxon.get('conservation_statuses') or [])
    if taxon.get('conservation_status'):
        records.append(taxon['conservation_status'])
    # Prefer global IUCN assessments; retain the source and regional scope otherwise.
    def priority(record):
        global_scope=not record.get('place_id') and not record.get('place')
        return (not (global_scope and 'iucn' in str(record.get('authority','')).lower()),not global_scope)
    for record in sorted(records,key=priority):
        raw=str(record.get('status') or '').upper().strip()
        equivalent=raw not in LABELS
        code=raw if not equivalent else IUCN_CODES.get(record.get('iucn'))
        if not code:
            continue
        place=record.get('place') or {}
        scope=place.get('display_name') or place.get('name') or ('Regional assessment' if record.get('place_id') else 'Global assessment')
        return dict(code=code,label=LABELS[code],source=record.get('authority') or 'iNaturalist conservation record',scope=scope,
                    equivalent=equivalent,reported_status=record.get('status'),source_url=record.get('url') if str(record.get('url','')).startswith('https://') else 'https://www.inaturalist.org/taxa/'+str(taxon.get('id','')))
    return dict(code='UNKNOWN',label=LABELS['UNKNOWN'],source='No assessment returned by iNaturalist',scope='Unknown',equivalent=False,source_url='https://www.inaturalist.org')
