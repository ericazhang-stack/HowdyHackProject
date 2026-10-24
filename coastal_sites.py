"""Ocean-coast directory. Shoreline alternatives are explicitly not tidepools.

Coordinates are approximate visitor destinations, not access routes. Official
sources establish the destination; check current access with its manager.
"""

def coastal_sites():
    # state, local timezone, name, lat, lon, official visitor page, habitat type
    rows = [
        ('Alaska','America/Anchorage',"Bishop's Beach",59.635,-151.548,'https://www.adfg.alaska.gov/index.cfm?adfg=viewinglocations.bishopsbeach','Tidepool shore'),
        ('Alaska','America/Anchorage','Bluff Point shore',59.665,-151.674,'https://www.adfg.alaska.gov/index.cfm?adfg=viewing.tidepooling','Tidepool shore'),
        ('Hawaii','Pacific/Honolulu',"Kapoʻo tidepools · Pūpūkea",21.651,-158.062,'https://dlnr.hawaii.gov/dar/marine-managed-areas/hawaii-marine-life-conservation-districts/oahu-pupukea/','Tidepool shore'),
        ('Hawaii','Pacific/Honolulu','Three Tables · Pūpūkea',21.645,-158.063,'https://dlnr.hawaii.gov/dar/marine-managed-areas/hawaii-marine-life-conservation-districts/oahu-pupukea/','Reef shoreline'),
        ('Oregon','America/Los_Angeles','Haystack Rock',45.884,-123.968,'https://www.ci.cannon-beach.or.us/hrap','Tidepool shore'),
        ('Washington','America/Los_Angeles','Rialto Beach',47.921,-124.639,'https://www.nps.gov/olym/planyourvisit/tidepool-activities.htm','Tidepool shore'),
        ('New Hampshire','America/New_York','Odiorne Point State Park',43.044,-70.714,'https://www.seacoastsciencecenter.org/visit/tide-pools/','Tidepool shore'),
        ('New Hampshire','America/New_York','Fort Stark State Historic Site',43.059,-70.711,'https://www.nhstateparks.org/find-parks-trails/fort-stark-state-historic-site','Rocky shoreline'),
        ('Massachusetts','America/New_York','Halibut Point State Park',42.688,-70.633,'https://www.mass.gov/locations/halibut-point-state-park','Tidepool shore'),
        ('Massachusetts','America/New_York','Red Rock Park',42.458,-70.939,'https://www.mass.gov/info-details/cz-tip-learn-what-lurks-in-a-massachusetts-tide-pool','Tidepool shore'),
        ('Rhode Island','America/New_York','Beavertail State Park',41.449,-71.400,'https://riparks.ri.gov/parks/beavertail-state-park','Rocky shoreline'),
        ('Rhode Island','America/New_York','Brenton Point State Park',41.449,-71.354,'https://riparks.ri.gov/parks/brenton-point-state-park','Rocky shoreline'),
        ('Connecticut','America/New_York','Hammonasset Beach State Park',41.259,-72.550,'https://ctparks.com/parks/hammonasset-beach-state-park','Beach and estuary'),
        ('Connecticut','America/New_York','Rocky Neck State Park',41.301,-72.244,'https://ctparks.com/parks/rocky-neck-state-park','Beach and estuary'),
        ('New York','America/New_York','Montauk Point State Park',41.071,-71.858,'https://parks.ny.gov/parks/montaukpoint','Rocky shoreline'),
        ('New York','America/New_York','Hither Hills State Park',41.008,-72.023,'https://parks.ny.gov/parks/hitherhills','Sandy shoreline'),
        ('New Jersey','America/New_York','Island Beach State Park',39.823,-74.095,'https://dep.nj.gov/parksandforests/state-park/island-beach-state-park/','Beach and estuary'),
        ('New Jersey','America/New_York','Barnegat Lighthouse State Park',39.764,-74.106,'https://dep.nj.gov/parksandforests/state-park/barnegat-lighthouse-state-park/','Inlet shoreline'),
        ('Delaware','America/New_York','Cape Henlopen State Park',38.778,-75.093,'https://destateparks.com/Beaches/CapeHenlopen','Beach and estuary'),
        ('Delaware','America/New_York','Delaware Seashore State Park',38.610,-75.064,'https://destateparks.com/Beaches/DelawareSeashore','Beach and estuary'),
        ('Maryland','America/New_York','Assateague State Park',38.240,-75.138,'https://dnr.maryland.gov/publiclands/Pages/eastern/assateague.aspx','Barrier island shore'),
        ('Maryland','America/New_York','Sandy Point State Park',39.012,-76.395,'https://dnr.maryland.gov/publiclands/Pages/southern/sandypoint.aspx','Bay shoreline'),
        ('Virginia','America/New_York','First Landing State Park',36.918,-76.052,'https://www.dcr.virginia.gov/state-parks/first-landing','Bay shoreline'),
        ('Virginia','America/New_York','Kiptopeke State Park',37.167,-75.981,'https://www.dcr.virginia.gov/state-parks/kiptopeke','Bay shoreline'),
        ('North Carolina','America/New_York','Fort Macon State Park',34.697,-76.681,'https://www.ncparks.gov/state-parks/fort-macon-state-park','Beach and inlet'),
        ('North Carolina','America/New_York','Hammocks Beach State Park',34.627,-77.144,'https://www.ncparks.gov/state-parks/hammocks-beach-state-park','Barrier island shore'),
        ('South Carolina','America/New_York','Hunting Island State Park',32.374,-80.438,'https://southcarolinaparks.com/hunting-island','Beach and estuary'),
        ('South Carolina','America/New_York','Huntington Beach State Park',33.508,-79.064,'https://southcarolinaparks.com/huntington-beach','Beach and estuary'),
        ('Georgia','America/New_York','Skidaway Island State Park',31.949,-81.052,'https://gastateparks.org/SkidawayIsland','Tidal marsh'),
        ('Georgia','America/New_York','Crooked River State Park',30.844,-81.556,'https://gastateparks.org/CrookedRiver','Tidal marsh'),
        ('Florida','America/New_York','Washington Oaks Gardens State Park',29.631,-81.205,'https://www.floridastateparks.org/parks-and-trails/washington-oaks-gardens-state-park','Coquina rock shore'),
        ('Florida','America/New_York','Bahia Honda State Park',24.660,-81.277,'https://www.floridastateparks.org/BahiaHonda','Tropical shoreline'),
        ('Alabama','America/Chicago','Gulf State Park',30.249,-87.667,'https://www.alapark.com/parks/gulf-state-park','Sandy shoreline'),
        ('Alabama','America/Chicago','Bon Secour National Wildlife Refuge',30.247,-87.829,'https://www.fws.gov/refuge/bon-secour','Barrier island shore'),
        ('Mississippi','America/Chicago','Buccaneer State Park',30.252,-89.405,'https://www.mdwfp.com/parks-destinations/state-parks/buccaneer','Gulf shoreline'),
        ('Mississippi','America/Chicago','Davis Bayou · Gulf Islands',30.393,-88.795,'https://www.nps.gov/guis/planyourvisit/davis-bayou-area.htm','Tidal marsh'),
        ('Louisiana','America/Chicago','Grand Isle State Park',29.262,-89.955,'https://www.lastateparks.com/parks-preserves/grand-isle-state-park','Barrier island shore'),
        ('Louisiana','America/Chicago','Fontainebleau State Park',30.343,-90.023,'https://www.lastateparks.com/parks-preserves/fontainebleau-state-park','Estuary shoreline'),
        ('Texas','America/Chicago','Galveston Island State Park',29.199,-94.960,'https://tpwd.texas.gov/state-parks/galveston-island','Beach and estuary'),
        ('Texas','America/Chicago','Mustang Island State Park',27.673,-97.175,'https://tpwd.texas.gov/state-parks/mustang-island','Barrier island shore'),
    ]
    northern_atlantic = {'New Hampshire','Massachusetts','Rhode Island','Connecticut','New York'}
    results = []
    for state, tz, name, lat, lng, source, kind in rows:
        habitat = 'pacific' if state in {'Oregon','Washington'} else 'atlantic' if state in northern_atlantic and kind != 'Sandy shoreline' else 'unlisted'
        results.append(dict(id='us-' + name.split(' · ')[0].lower().replace(' ', '-').replace("'", ''), name=name,
                            lat=lat, lng=lng, region=state, country='United States', timezone=tz,
                            station=None, station_name=None, habitat=habitat, kind=kind, source=source))
    return results
