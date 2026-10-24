let sites = [], species = [], currentSpot, map, chart, nextLow, guideHeight, activeZoneFilter = 'all', requestNumber = 0;
let nearbySpecies=[], wildlifeMessage='Choose a destination to load nearby records.', selectedStationMarker;
const el = id => document.getElementById(id);
const localTime = value => new Date(value).toLocaleString('en-US', {timeZone:currentSpot?.timezone || 'America/Los_Angeles', month:'short', day:'numeric', hour:'numeric', minute:'2-digit', timeZoneName:'short'});
async function api(path) {
    const response = await fetch(path);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed');
    return data;
}
function handlePresetChange() {
    currentSpot = sites.find(s => s.id === el('preset-select').value);
    el('input-lat').value = currentSpot.lat;
    el('input-lng').value = currentSpot.lng;
    el('active-spot-name').textContent = currentSpot.name;
    el('date-label').textContent = `Visit date · ${currentSpot.timezone.replaceAll('_',' ')}`;
    el('site-info').href = currentSpot.source;
    el('site-info').textContent = `${currentSpot.region}, ${currentSpot.country} · ${currentSpot.kind} · Visitor information ↗`;
    el('noaa-station-badge').textContent=currentSpot.station ? `NOAA #${currentSpot.station}` : 'Location guide only';
    if (map) map.setView([currentSpot.lat, currentSpot.lng], 12);
    refreshData();
}
function handleCustomCoords() {
    const lat = Number(el('input-lat').value), lng = Number(el('input-lng').value);
    if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat)>90 || Math.abs(lng)>180) {
        el('recommendation-text').textContent = 'Enter valid latitude and longitude.'; return;
    }
    // Find a supported destination, never pretend arbitrary coordinates are verified pools.
    const distance = s => {
        const rad = x => x*Math.PI/180;
        const a = Math.sin(rad(s.lat-lat)/2)**2 + Math.cos(rad(lat))*Math.cos(rad(s.lat))*Math.sin(rad(s.lng-lng)/2)**2;
        return 6371*2*Math.asin(Math.sqrt(Math.min(1,a)));
    };
    const closest = [...sites].sort((a,b) => distance(a)-distance(b))[0];
    if (distance(closest)>150) {
        el('recommendation-text').textContent = 'No listed destination within 150 km. Browse the international destination menu.'; return;
    }
    closest.select();
}
function useMyLocation() {
    if (!navigator.geolocation) { el('recommendation-text').textContent = 'Location is unavailable; choose a destination.'; return; }
    navigator.geolocation.getCurrentPosition(pos => {
        el('input-lat').value=pos.coords.latitude; el('input-lng').value=pos.coords.longitude; handleCustomCoords();
    }, () => {el('recommendation-text').textContent='Location permission unavailable; choose a destination.';});
}
async function refreshData() {
    const request = ++requestNumber;
    nextLow = null;
    guideHeight = undefined;
    nearbySpecies=[];
    wildlifeMessage='Loading nearby iNaturalist observations and photos…';
    loadWildlife(currentSpot.id, request);
    el('tide-table-body').replaceChildren();
    el('chart-note').textContent='Loading tide predictions…';
    if (chart) {chart.destroy(); chart=null;}
    el('score-number').textContent='—'; el('score-status').textContent='LOADING TIDES';
    el('low-tide-time-label').textContent='Loading…';
    el('recommendation-text').textContent='Fetching station predictions…';
    renderSpecies();
    try {
        const data = await api(`/api/tides?site=${currentSpot.id}&date=${el('visit-date').value}`);
        if (request !== requestNumber) return;
        if (data.available === false) {
            el('score-status').textContent='LOCATION GUIDE';
            el('low-tide-time-label').textContent='Local tide tables required';
            el('recommendation-text').textContent=data.message;
            el('chart-note').textContent='No prediction data available. Global coverage requires a configured WorldTides account.';
            return;
        }
        el('noaa-station-badge').textContent=data.source==='WorldTides' ? 'WorldTides global model' : `NOAA #${data.site.station} · ${data.site.station_name}`;
        el('datum-label').textContent=`${data.source} · feet relative to ${data.datum}`;
        el('chart-note').textContent=data.chart_note || `${data.source} predictions in destination local time. ${data.attribution || ''}`;
        const dateKey = value => new Intl.DateTimeFormat('en-CA',{timeZone:currentSpot.timezone,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value));
        const points = data.curve.filter(p => dateKey(p.time)===el('visit-date').value);
        const lows = data.lows.filter(p => dateKey(p.time)===el('visit-date').value);
        nextLow = lows.find(p => new Date(p.time)>new Date()) || null;
        const best = lows.reduce((a,b) => !a || b.height<a.height ? b : a, null);
        const current = data.curve.reduce((a,b) => !a || Math.abs(new Date(b.time)-Date.now())<Math.abs(new Date(a.time)-Date.now())?b:a, null);
        const today = dateKey(new Date())===el('visit-date').value;
        el('score-number').textContent=best ? best.height.toFixed(1) : '—';
        el('score-status').textContent=`LOWEST TIDE · FT ${data.datum}`;
        el('low-tide-time-label').textContent=nextLow ? `${localTime(nextLow.time)} (${nextLow.height.toFixed(1)} ft)` : 'No upcoming low on selected date';
        const distance=data.site.station_distance_km;
        const proxy=distance !== undefined ? ` Regional tide station: ${distance} km away by straight-line distance. Proximity does not establish matching tides or access.` : ' Model predictions do not describe individual pools.';
        el('recommendation-text').textContent=`${best ? 'Lowest tide: '+localTime(best.time)+'. ' : ''}${proxy} Check daylight, park hours, surf and closures before visiting. Updated ${localTime(data.fetched_at)}.`;
        const dayEvents=(data.events || []).filter(p=>dateKey(p.time)===el('visit-date').value);
        const estimated=data.curve_kind==='interpolated';
        if (points.length && typeof Chart !== 'undefined') chart = new Chart(el('tideChart'), {
            type:'line',data:{datasets:[
                {label:`${estimated?'Estimated curve':'Provider curve'} · ft ${data.datum}`,data:points.map(p=>({x:Date.parse(p.time),y:p.height})),borderColor:'#357da8',backgroundColor:'rgba(113,177,205,.18)',borderDash:estimated?[7,5]:[],fill:true,tension:0,pointRadius:0,spanGaps:false},
                {label:'Turning points in table',data:dayEvents.map(p=>({x:Date.parse(p.time),y:p.height})),showLine:false,pointRadius:6,pointHoverRadius:9,pointBackgroundColor:dayEvents.map(p=>p.type==='H'?'#607cb9':'#359ca3'),pointBorderColor:'#fff',pointBorderWidth:2}
            ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#425f76'}},tooltip:{callbacks:{title:items=>localTime(items[0].parsed.x),label:item=>`${item.dataset.label}: ${item.parsed.y.toFixed(2)}`}}},scales:{y:{title:{display:true,text:`Feet · ${data.datum}`},ticks:{color:'#526d78'}},x:{type:'linear',ticks:{color:'#526d78',maxTicksLimit:6,callback:value=>new Date(value).toLocaleTimeString('en-US',{timeZone:currentSpot.timezone,hour:'numeric',minute:'2-digit'})}}}}
        });
        (data.events || []).filter(p=>dateKey(p.time)===el('visit-date').value).forEach(p=>{
            const row=document.createElement('tr');
            [localTime(p.time),p.type==='L'?'Low tide':'High tide',`${p.height.toFixed(2)} ft ${data.datum}`].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;row.append(cell);});
            el('tide-table-body').append(row);
        });
        guideHeight = data.datum==='MLLW' && !estimated ? (today && current ? current.height : best?.height) : undefined;
        renderSpecies();
    } catch(error) {
        if(request!==requestNumber)return;
        el('score-status').textContent='DATA UNAVAILABLE';
        el('low-tide-time-label').textContent='Unavailable';
        el('recommendation-text').textContent=error.message;
        el('chart-note').textContent='Tide data unavailable; no simulated curve or table is shown.';
    }
}
async function loadWildlife(siteId, request) {
    try {
        const data=await api('/api/wildlife?site='+encodeURIComponent(siteId));
        if(request!==requestNumber)return;
        nearbySpecies=data.species;
        wildlifeMessage=`${data.message} Showing ${data.species.length} taxa from ${data.sampled_observations} sampled records (${data.total_matching_observations} matching records in total).`;
    } catch(error) {
        if(request!==requestNumber)return;
        wildlifeMessage=error.message;nearbySpecies=[];
    }
    renderSpecies();
}
function renderSpecies(height = guideHeight) {
    const grid=el('species-grid'); grid.replaceChildren();
    const nearby=el('wildlife-view').value==='nearby';
    el('wildlife-status').textContent=nearby?wildlifeMessage:'Regional habitat examples. These are not confirmed local sightings.';
    document.querySelector('.tabs').hidden=nearby;
    const regionalSpecies=nearby?nearbySpecies:species.filter(s=>s.habitat===currentSpot?.habitat);
    if(!regionalSpecies.length) {
        const note=document.createElement('p');note.className='empty-guide';note.textContent=nearby?'No nearby photo records to show yet. This does not mean no wildlife is present.':'A regional species guide has not been added here yet. Try nearby records or explore iNaturalist.';
        const link=document.createElement('a');link.href=`https://www.inaturalist.org/observations?lat=${currentSpot.lat}&lng=${currentSpot.lng}&radius=10`;link.textContent='Browse nearby wildlife records ↗';link.target='_blank';link.rel='noopener';note.append(document.createElement('br'),link);grid.append(note);
    }
    regionalSpecies.filter(s=>nearby||activeZoneFilter==='all'||s.zone===activeZoneFilter).forEach(s=>{
        const card=document.createElement('article');
        card.className='bg-ocean-deep rounded-2xl border border-teal-500/20 p-5';
        if(s.photo) {
            const figure=document.createElement('figure');figure.className='organism-photo';
            const image=document.createElement('img');image.src=s.photo.url;image.alt=`${s.name} (${s.sci})`;image.loading='lazy';image.width=600;image.height=400;
            const caption=document.createElement('figcaption');
            const credit=document.createElement('a');credit.href=s.photo.source;credit.target='_blank';credit.rel='noopener';credit.textContent=s.photo.attribution;
            caption.append(credit);figure.append(image,caption);card.append(figure);
            image.onerror=()=>{image.hidden=true;caption.textContent='Photo unavailable. '+s.photo.attribution;};
        }
        const title=document.createElement('h3'); title.className='text-teal-200 font-bold text-lg'; title.textContent=s.name;
        const sci=document.createElement('p'); sci.className='italic text-slate-400 text-xs'; sci.textContent=s.sci;
        const desc=document.createElement('p'); desc.className='text-sm text-slate-300 my-3'; desc.textContent=s.desc;
        const note=document.createElement('p'); note.className='text-xs text-sand-300';
        note.textContent=s.nearby ? `Last sampled record: ${s.observed_on || 'date unknown'} · ${s.sample_count} records in this sample. Intertidal zone unknown.` : `${s.zone} intertidal · Habitat guide; sighting not guaranteed. ${height !== undefined && s.zone==='low' && height>0.5 ? 'Lower pools may remain submerged at this predicted height.' : ''}`;
        const link=document.createElement('a'); link.className='text-xs text-teal-300 underline'; link.href=`https://www.inaturalist.org/observations?lat=${currentSpot.lat}&lng=${currentSpot.lng}&radius=10&taxon_name=${encodeURIComponent(s.sci)}`;link.target='_blank';link.rel='noopener';link.textContent='Explore nearby iNaturalist records ↗';
        if(s.observation_url){link.href=s.observation_url;link.textContent='View source observation ↗';}
        card.append(title,sci,desc,note,link);grid.append(card);
    });
}
function filterSpecies(zone) {
    activeZoneFilter=zone;
    ['all','high','mid','low'].forEach(z=>{el('tab-'+z).classList.toggle('bg-teal-600',z===zone);el('tab-'+z).setAttribute('aria-pressed',z===zone);});
    renderSpecies();
}
window.onload=async()=>{
    el('recommendation-text').setAttribute('role','status');
    try {
        const data=await api('/api/sites');sites=data.sites;species=data.species;
        el('preset-select').replaceChildren();
        const stateLabel=document.createElement('label');stateLabel.className='state-filter';stateLabel.textContent='Browse a state or country';
        const stateSelect=document.createElement('select');stateSelect.setAttribute('aria-label','Filter destinations by state or country');stateSelect.add(new Option('All destinations','all'));
        const states=[...new Set(sites.filter(s=>s.country==='United States').map(s=>s.region))].sort();
        states.forEach(state=>stateSelect.add(new Option(state,state)));
        [...new Set(sites.filter(s=>s.country!=='United States').map(s=>s.country))].sort().forEach(country=>stateSelect.add(new Option(country,country)));
        stateLabel.append(stateSelect);document.querySelector('.controls').prepend(stateLabel);
        function populateDestinations(){
            const filtered=sites.filter(s=>stateSelect.value==='all'||s.region===stateSelect.value||s.country===stateSelect.value);
            el('preset-select').replaceChildren();
            const groups=[...new Set(filtered.map(s=>s.country==='United States'?s.region:s.country))].sort();
            groups.forEach(name=>{
                const group=document.createElement('optgroup');group.label=name;
                filtered.filter(s=>(s.country==='United States'?s.region:s.country)===name).forEach(s=>group.append(new Option(`${s.name}${s.station?' · NOAA tides':' · location guide'}`,s.id)));
                el('preset-select').append(group);
            });
            if(filtered.some(s=>s.id===currentSpot?.id))el('preset-select').value=currentSpot.id;
        }
        stateSelect.onchange=()=>{populateDestinations();handlePresetChange();};populateDestinations();
        // Markers and location lookup can select a destination outside the filter.
        function chooseSite(s){
            if(!sites.some(existing=>existing.id===s.id))sites.push(s);
            stateSelect.value='all';populateDestinations();el('preset-select').value=s.id;handlePresetChange();
            if(map && (s.id.startsWith('noaa-') || s.id.startsWith('coordinates:'))){
                if(selectedStationMarker)map.removeLayer(selectedStationMarker);
                selectedStationMarker=L.marker([s.lat,s.lng]).addTo(map).bindPopup(document.createTextNode(s.name));
            }
        }
        window.exploreCoordinates=async()=>{
            try{
                const site=await api(`/api/location?lat=${encodeURIComponent(el('input-lat').value)}&lng=${encodeURIComponent(el('input-lng').value)}`);
                site.select=()=>chooseSite(site);chooseSite(site);
            }catch(error){el('recommendation-text').textContent=error.message;}
        };
        sites.forEach(s=>{s.select=()=>chooseSite(s);});
        let stationRequest=0,stationOffset=0,stationTimer;
        async function searchStations(offset=0){
            const request=++stationRequest;stationOffset=offset;
            el('station-results').replaceChildren();el('station-status').textContent='Searching NOAA stations…';
            try{
                const result=await api(`/api/stations?q=${encodeURIComponent(el('station-search').value)}&offset=${offset}`);
                if(request!==stationRequest)return;
                el('station-status').textContent=`${result.total} matching prediction stations. Showing ${result.stations.length ? offset+1 : 0}–${Math.min(offset+30,result.total)}. Catalogue updated ${result.catalogue_updated_at?.slice(0,10) || 'unknown'}. NOAA station times are displayed in UTC.`;
                result.stations.forEach(station=>{const button=document.createElement('button');button.className='station-result';button.textContent=`${station.name} · ${station.region} · #${station.station} · ${station.station_type==='S'?'high/low table':'tide predictions'}`;button.onclick=()=>{station.select=()=>chooseSite(station);chooseSite(station);};el('station-results').append(button);});
                el('stations-next').disabled=offset+30>=result.total;
                el('stations-prev').disabled=offset===0;
            }catch(error){if(request===stationRequest)el('station-status').textContent=error.message;}
        }
        el('station-search').oninput=()=>{clearTimeout(stationTimer);stationTimer=setTimeout(()=>searchStations(),300);};
        el('stations-next').onclick=()=>searchStations(stationOffset+30);el('stations-prev').onclick=()=>searchStations(Math.max(0,stationOffset-30));
        searchStations();
        if(typeof L!=='undefined') {
            const worldBounds=L.latLngBounds([[-85,-180],[85,180]]);
            map=L.map('map',{minZoom:0,maxZoom:19,maxBounds:worldBounds,maxBoundsViscosity:1.0,worldCopyJump:false}).setView([36.5,-121],6);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors',maxZoom:19,noWrap:true,bounds:worldBounds}).addTo(map);
            const fitSingleWorld=()=>map.setMinZoom(Math.max(0,map.getBoundsZoom(worldBounds)));
            fitSingleWorld();map.on('resize',fitSingleWorld);
            sites.forEach(s=>{
                const box=document.createElement('div');const a=document.createElement('a');a.href=s.source;a.textContent=s.name+' · Park information';a.target='_blank';a.rel='noopener';box.append(a);
                L.marker([s.lat,s.lng]).addTo(map).bindPopup(box).on('click',()=>s.select());
            });
        } else el('map').textContent='Map library unavailable. Use the destination menu above.';
        el('visit-date').value=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
        el('preset-select').value='fitzgerald';handlePresetChange();
        const heroTags=document.querySelector('.hero-tags');heroTags.replaceChildren();
        [`${sites.length} curated destinations`,`${data.station_count} NOAA stations`,'Nearby wildlife photos'].forEach(text=>{const tag=document.createElement('span');tag.textContent=text;heroTags.append(tag);});
        const sticker=(name,cls)=>{const node=document.createElement('span');node.className='sea-sticker '+cls;node.setAttribute('aria-hidden','true');node.innerHTML=`<svg viewBox="0 0 160 160"><use href="/sea-friends.svg#${name}"></use></svg>`;return node;};
        const friends=document.createElement('div');friends.className='hero-friends';
        ['octopus','turtle','crab','star'].forEach((name,i)=>friends.append(sticker(name,'friend-'+i)));document.querySelector('.hero').append(friends);
        document.querySelectorAll('main > section, .care').forEach((section,i)=>section.append(sticker(['fish','star','crab','turtle'][i%4],['friend-left','friend-bottom-right','friend-heading','friend-bottom-left','friend-inline'][i%5])));
        setInterval(()=>{
            const seconds=nextLow?Math.max(0,Math.floor((new Date(nextLow.time)-Date.now())/1000)):null;
            ['cd-hours','cd-mins','cd-secs'].forEach((id,i)=>el(id).textContent=seconds===null?'—':String(i===0?Math.floor(seconds/3600):i===1?Math.floor(seconds/60)%60:seconds%60).padStart(2,'0'));
        },1000);
    } catch(error) {el('recommendation-text').textContent='Start the Python server with python app.py and open http://127.0.0.1:8000. '+error.message;}
};
