"""Optional public-source smoke checks. US NOAA and iNaturalist only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import app

def tide_check(site):
    try:
        result=app.forecast(site,datetime.now(timezone.utc).date().isoformat())
        return site['station'], bool(result.get('events')), len(result.get('curve',[]))
    except Exception:
        return site['station'],False,0

if __name__=='__main__':
    unique={s['station']:s for s in app.SITES if s['station']}
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(tide_check,unique.values()))
    print('NOAA tide tables:',sum(ok for _,ok,_ in results),'/',len(results),'unique curated proxy stations')
    print('Stations without event results:',[station for station,ok,_ in results if not ok])
    for key in ['fitzgerald','us-galveston-island-state-park']:
        try:
            result=app.wildlife(app.find_site(key))
            print(key,':',len(result['species']),'photographed taxa from',result['sampled_observations'],'sampled records')
        except Exception as error:
            print(key,': public observation request unavailable (',type(error).__name__,')')
