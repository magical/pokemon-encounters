from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from codecs import open

engine = create_engine('postgresql:///veekun-pokedex')
Session = sessionmaker(bind=engine)
session = Session()

from pokedex.db.tables import Location, LocationInternalID

with open("bw-locations-en", "r", "utf-8") as f:
    names = [line.rstrip("\n") for line in f]

locations = {}
for i, name in enumerate(names):
    if i == 0 or not name:
        continue

    if name in locations:
        loc = locations[name]
    else:
        loc = Location()
        loc.name = name
        loc.region_id = 5 # Unova

        locations[name] = loc

    lid = LocationInternalID()
    lid.location = loc
    lid.generation_id = 5 # Gen 5
    lid.internal_id = i

    session.add(loc)
    session.add(lid)

session.commit()

