"""Bundle public destination data for opening index.html without a server."""
import json
from pathlib import Path
import app

def prepare(output=None):
    path=Path(output) if output else app.ROOT/'preview-data.js'
    data=dict(sites=app.SITES,species=app.SPECIES,station_count=len(app.STATIONS),catalogue_updated_at=app.CATALOGUE['fetched_at'])
    path.write_text('// Public file-preview data; live requests still use the Python API.\nwindow.TIDEPOOL_PREVIEW = '+json.dumps(data,ensure_ascii=True)+';\n',encoding='utf-8')
    return path

if __name__=='__main__':
    print('Prepared',prepare().name)
