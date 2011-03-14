from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from codecs import open

engine = create_engine('postgresql:///veekun-pokedex')
Session = sessionmaker(bind=engine)
session = Session()

from pokedex.db.tables import Location, LocationInternalID

with open("bw-location-names-kanji-translated", "r", "utf-8") as f:
    names = [line.rstrip("\n") for line in f]

for i, name in enumerate(names):
    if i == 0:
        continue

    loc = Location()
    loc.name = name
    loc.region_id = 5 # Unova

    lid = LocationInternalID()
    lid.location = loc
    lid.generation_id = 5 # Gen 5
    lid.internal_id = i

    session.add(loc)
    session.add(lid)

session.commit()

