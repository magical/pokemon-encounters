# The encounter schema, as it currently exists in veekun

from sqlalchemy import Column, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import *

metadata = MetaData()
TableBase = declarative_base(metadata=metadata)

class Encounter(TableBase):
    """Rows in this table represent encounters with wild Pokémon.  Bear with
    me, here.

    Within a given area in a given game, encounters are differentiated by the
    "slot" they are in and the state of the game world.

    What the player is doing to get an encounter, such as surfing or walking
    through tall grass, is called terrain.  Each terrain has its own set of
    encounter slots.

    Within a terrain, slots are defined primarily by rarity.  Each slot can
    also be affected by world conditions; for example, the 20% slot for walking
    in tall grass is affected by whether a swarm is in effect in that area.
    "Is there a swarm?" is a condition; "there is a swarm" and "there is not a
    swarm" are the possible values of this condition.

    A slot (20% walking in grass) and any appropriate world conditions (no
    swarm) are thus enough to define a specific encounter.

    Well, okay, almost: each slot actually appears twice.
    """

    __tablename__ = 'encounters'
    id = Column(Integer, primary_key=True, nullable=False)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    location_area_id = Column(Integer, ForeignKey('location_areas.id'), nullable=False)
    encounter_slot_id = Column(Integer, ForeignKey('encounter_slots.id'), nullable=False)
    #pokemon_id = Column(Integer, ForeignKey('pokemon.id'), nullable=False)
    pokemon_id = Column(Integer, nullable=False)
    min_level = Column(Integer, nullable=False)
    max_level = Column(Integer, nullable=False)

class EncounterCondition(TableBase):
    """Rows in this table represent varying conditions in the game world, such
    as time of day.
    """

    __tablename__ = 'encounter_conditions'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(64), nullable=False)

class EncounterConditionValue(TableBase):
    """Rows in this table represent possible states for a condition; for
    example, the state of 'swarm' could be 'swarm' or 'no swarm'.
    """

    __tablename__ = 'encounter_condition_values'
    id = Column(Integer, primary_key=True, nullable=False)
    encounter_condition_id = Column(Integer, ForeignKey('encounter_conditions.id'), primary_key=False, nullable=False)
    name = Column(Unicode(64), nullable=False)
    is_default = Column(Boolean, nullable=False)

class EncounterConditionValueMap(TableBase):
    """Maps encounters to the specific conditions under which they occur."""

    __tablename__ = 'encounter_condition_value_map'
    encounter_id = Column(Integer, ForeignKey('encounters.id'), primary_key=True, nullable=False)
    encounter_condition_value_id = Column(Integer, ForeignKey('encounter_condition_values.id'), primary_key=True, nullable=False)

class EncounterTerrain(TableBase):
    """Rows in this table represent ways the player can enter a wild encounter,
    e.g., surfing, fishing, or walking through tall grass.
    """

    __tablename__ = 'encounter_terrain'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(64), nullable=False)

class EncounterSlot(TableBase):
    """Rows in this table represent an abstract "slot" within a terrain,
    associated with both some set of conditions and a rarity.

    Note that there are two encounters per slot, so the rarities will only add
    up to 50.
    """

    __tablename__ = 'encounter_slots'
    id = Column(Integer, primary_key=True, nullable=False)
    version_group_id = Column(Integer, ForeignKey('version_groups.id'), nullable=False)
    encounter_terrain_id = Column(Integer, ForeignKey('encounter_terrain.id'), primary_key=False, nullable=False)
    slot = Column(Integer, nullable=True)
    rarity = Column(Integer, nullable=False)

class EncounterSlotCondition(TableBase):
    """Lists all conditions that affect each slot."""

    __tablename__ = 'encounter_slot_conditions'
    encounter_slot_id = Column(Integer, ForeignKey('encounter_slots.id'), primary_key=True, nullable=False)
    encounter_condition_id = Column(Integer, ForeignKey('encounter_conditions.id'), primary_key=True, nullable=False)


class LocationArea(TableBase):
    __tablename__ = 'location_areas'
    id = Column(Integer, primary_key=True, nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    internal_id = Column(Integer, nullable=False)
    name = Column(Unicode(64), nullable=True)

class LocationAreaEncounterRate(TableBase):
    __tablename__ = 'location_area_encounter_rates'
    location_area_id = Column(Integer, ForeignKey('location_areas.id'), primary_key=True, nullable=False)
    encounter_terrain_id = Column(Integer, ForeignKey('encounter_terrain.id'), primary_key=True, nullable=False)
    version_id = Column(Integer, ForeignKey('versions.id'), primary_key=True)
    rate = Column(Integer, nullable=True)

class LocationInternalID(TableBase):
    __tablename__ = 'location_internal_ids'
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, primary_key=True)
    generation_id = Column(Integer, ForeignKey('generations.id'), nullable=False, primary_key=True)
    internal_id = Column(Integer, nullable=False)




class Generation(TableBase):
    __tablename__ = 'generations'
    id = Column(Integer, primary_key=True, nullable=False)
    main_region_id = Column(Integer, ForeignKey('regions.id'))
    #canonical_pokedex_id = Column(Integer, ForeignKey('pokedexes.id'))
    name = Column(Unicode(16), nullable=False)

class Region(TableBase):
    """Major areas of the world: Kanto, Johto, etc."""
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(16), nullable=False)

class Version(TableBase):
    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True, nullable=False)
    version_group_id = Column(Integer, ForeignKey('version_groups.id'), nullable=False)
    name = Column(Unicode(32), nullable=False)

class VersionGroup(TableBase):
    __tablename__ = 'version_groups'
    id = Column(Integer, primary_key=True, nullable=False)
    generation_id = Column(Integer, ForeignKey('generations.id'), nullable=False)

