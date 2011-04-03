from warnings import warn

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql:///veekun-pokedex')
Session = sessionmaker(bind=engine)
session = Session()


from pokedex.db.tables import EncounterSlot

rarities = {
    'walk': [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1],
    'super-rod': [40, 40, 15, 4, 1],
    'surf': [60, 30, 5, 4, 1],
}

for slot in session.query(EncounterSlot).all():
    if slot.version_group_id in (11,):
        rarity = rarities[slot.method.identifier][slot.slot-1]

        if rarity is not None:
            if slot.rarity is not None and slot.rarity != rarity:
                warn("replacing %d: %d%% with %d%%" % (slot.slot, slot.rarity, rarity))
            slot.rarity = rarity
            session.add(slot)

session.commit()

