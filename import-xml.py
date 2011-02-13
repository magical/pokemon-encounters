#!/usr/bin/env python2

from __future__ import unicode_literals

import sys
import itertools
from copy import deepcopy
from operator import itemgetter
from lxml.etree import parse as parse_xml

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

sql_lower = sqlalchemy.func.lower

from pokedex.db.tables import Encounter, EncounterCondition, EncounterConditionValue
from pokedex.db.tables import EncounterTerrain, EncounterSlot
from pokedex.db.tables import Location, LocationArea
from pokedex.db.tables import Version

SessionClass = sessionmaker()

# Global are evil, but practically everything needs to access the session.
# The alternative is to reformulate the whole module as a class, which brings
# its own problems.
session = SessionClass()

class memoize(object):
    """A simple memoizer.

    The wrapped function can only accept positional, hashable arguments.
    """

    def __init__(self, func):
        self.func = func
        self.memo = {}

    def __call__(self, *args):
        if args in self.memo:
            return self.memo[args]
        else:
            value = self.func(*args)
            self.memo[args] = value
            return value

# map veekun's condition names to mine
condition_value_map = {
    ('time', 'morning'): 'time-morning',
    ('time', 'day'):     'time-day',
    ('time', 'night'):   'time-night',
    ('swarm', ''):      'swarm-no',
    ('swarm', 'swarm'): 'swarm-yes',
    ('radar', ''):      'radar-off',
    ('radar', 'radar'): 'radar-on',
    ('radio', ''):       'radio-off',
    ('radio', 'hoenn'):  'radio-hoenn',
    ('radio', 'sinnoh'): 'radio-sinnoh',
    ('slot2', ''):          'slot2-none',
    ('slot2', 'ruby'):      'slot2-ruby',
    ('slot2', 'sapphire'):  'slot2-sapphire',
    ('slot2', 'emerald'):   'slot2-emerald',
    ('slot2', 'firered'):   'slot2-firered',
    ('slot2', 'leafgreen'): 'slot2-leafgreen',
}

condition_values = {
    'season': [],
    'time': ['morning', 'day', 'night'],
    'swarm': ['', 'swarm'],
    'radar': ['', 'radar'],
    'radio': ['', 'hoenn', 'sinnoh'],
    'slot2': ['', 'ruby', 'sapphire', 'emerald', 'firered', 'leafgreen'],
}

@memoize
def get_condition(cond_value):
    """Fetch the EncounterConditionValue for a given (cond,value) pair."""

    identifier = condition_value_map[cond_value]

    q = session.query(EncounterConditionValue)
    q = (q.join(EncounterCondition)
          .filter(EncounterConditionValue.identifier == identifier))
    return q.one()

@memoize
def get_conditions():
    """Fetch all valid conditions identifiers."""
    return condition_values.keys()

def get_condition_values(cond):
    """Fetch the list of values for the given condition."""
    return condition_values[cond]

@memoize
def get_version(version):
    """Fetch the Version object for a given version identifier."""
    q = session.query(Version)
    q = q.filter(sql_lower(Version.name) == version)
    return q.one()

@memoize
def get_terrain_id(terrain):
    """Fetch the id for a given terrain"""
    q = session.query(EncounterTerrain.id).filter_by(identifier=terrain)
    return q.one().id

@memoize
def get_method_id(method):
    """Fetch the id for a given method"""
    # XXX EncounterTerrain
    q = session.query(EncounterTerrain.id).filter_by(identifier=method)
    return q.one().id

@memoize
def _get_or_create_encounter_slot(slot, method, version_group_id, terrain):
    terrain_id = None
    #if terrain is not None:
    #    terrain_id = get_terrain_id(terrain)

    method_id = get_method_id(method)

    q = session.query(EncounterSlot).filter_by(
        slot=slot,
        version_group_id=version_group_id,
        # XXX encounter_terrain_id
        encounter_terrain_id=method_id,
        #encounter_terrain_id=terrain_id,
    )
    try:
        x = q.one()
    except NoResultFound:
        x = EncounterSlot()
        x.slot = slot
        x.version_group_id = version_group_id
        # XXX encounter_terrain_id
        x.encounter_terrain_id = method_id
        #x.encounter_terrain_id = terrain_id
    return x

def get_or_create_encounter_slot(slot, method, version_group_id, terrain=None):
    return _get_or_create_encounter_slot(slot, method, version_group_id, terrain)

def parse_range(s):
    min, _, max = s.partition('-')
    min = int(min)
    if max:
        max = int(max)
        return min, max
    else:
        return min, min

def lift_conditions(e):
    all_conditions = get_conditions()
    conditions = {}
    for name in all_conditions:
        if name in e.attrib:
            conditions[name] = e.attrib[name]
    return conditions

def groupby(it, key):
    """My version of itertools.groupby(), which sorts the list first."""
    return itertools.groupby(sorted(it, key=key), key)

def identical(it, key=lambda x: x):
    return len(set(map(key, it))) == 1

def visit_monsters(elem):
    assert elem.tag == 'monsters'

    obj = {}
    if 'method' in elem.attrib:
        obj['method'] = elem.get('method')
    if 'terrain' in elem.attrib:
        obj['terrain'] = elem.get('terrain')
    if 'rate' in elem.attrib:
        obj['rate'] = int(elem.get('rate'))

    obj['conditions'] = lift_conditions(elem)

    obj['pokemon'] = pokemon_list = []
    for slot, pokemon in enumerate(elem.xpath('./pokemon')):
        pokemon_list.append(visit_pokemon(pokemon, slot+1))

    obj['subgroups'] = subgroups = []
    for monsters in elem.xpath('./monsters'):
        subgroups.append(visit_monsters(monsters))

    #munge_monsters(obj)

    return obj

#def munge_monsters(obj):
#    if 'spots' in obj['conditions']:
#        terrain = obj['terrain']
#        if not terrain:
#            terrain = obj['method']
#
#        obj['method'] 
#        obj['method'] += '-spots'



def visit_pokemon(elem, slot=None):
    assert elem.tag == 'pokemon'

    if elem.get('slot') is not None:
        slot = int(elem.get('slot'))

    obj = {
        'slot': slot,
        'pokemon_id': int(elem.get('number')),
        'form': elem.get('form'),
        'levels': parse_range(elem.get('levels')),
    }
    return obj

def lift(root):
    """Lift encounter xml into json objects"""
    encounter_list = []
    for monsters in root:
        encounter_list.append(visit_monsters(monsters))
    return encounter_list

class EncounterMonkey(object):
    def __init__(self, encounters):
        # we'll make a deepcopy of the encounter list, so we aren't affected by
        # our caller's shennanigans
        self.encounters = deepcopy(encounters)
        # Now a lexicographical sort of the encounters.
        self.encounters.sort(key=self._sort_key, reverse=True)

    def strip_redundancy(self):
        # This is easy to check when you have a sorted list:
        # For each encounter, simply find the next one down that applies.
        # If they are equivalent, the first is redundant.

        # This would be prettier as a recursive function on a linked list.

        key = self._eq_key

        # 1. Mark
        for i, e in enumerate(self.encounters):
            conditions = e['conditions']
            for e2 in self.encounters[i+1:]:
                if self._match(e2, conditions) and key(e) == key(e2):
                    e['is_redundant'] = True

        # 2. Sweep
        self.encounters = [e for e in self.encounters
                           if not e.get('is_redundant', False)]

    def collapse_encounters(self):
        # we really only have to check for season and time, since the others
        # should be caught in strip_redundancy().
        encounters = self.encounters
        for cond in ('time',):
            encounters = self._collapse_encounters(encounters, cond)
        encounters.sort(key=self._sort_key, reverse=True)
        self.encounters = encounters

    def _collapse_encounters(self, encounters, cond):

        # group by conditions other than cond
        def key(e):
            if cond in e['conditions']:
                conditions = e['conditions'].copy()
                del conditions[cond]
                return conditions
            else:
                return None

        all_values = set(get_condition_values(cond))
        def can_collapse(group):
            values = set(e['conditions'][cond] for e in group)
            if values == all_values and identical(group, key=self._eq_key):
                return True
            else:
                return False

        new_encounters = []
        for common_conds, group in groupby(encounters, key):
            group = list(group)
            if (common_conds is not None and
                len(group) > 1 and
                can_collapse(group)):

                e = group[0]
                e['conditions'] = common_conds
                new_encounters.append(e)
            else:
                new_encounters.extend(group)

        return new_encounters

    def get_encounter(self, conditions):
        for e in self.encounters:
            if self._match(e, conditions):
                return e

    def get_conditions(self):
        """Return all conditions which can apply to an encounter"""
        conditions = dict()
        for e in self.encounters:
            for k, v in e['conditions'].iteritems():
                if k not in conditions:
                    conditions[k] = set()
                conditions[k].add(v)
        return conditions.keys() #XXX

    @staticmethod
    def _match(encounter, conditions):
        e_conditions = encounter['conditions']
        for cond, value in conditions.iteritems():
            if cond in e_conditions and e_conditions[cond] != value:
                return False
        return True

    @staticmethod
    def _sort_key(e):
        priority_groups = [
            ['season'],
            ['time'],
            ['swarm', 'radar'], #XXX etc
        ]

        key = []
        for conditions in priority_groups:
            # the number of conditions in this group which are part of the
            # encounter's conditions
            n = sum(int(c in e['conditions']) for c in conditions)
            key.append(n)

        key.reverse()

        return tuple(key)

    _eq_key = staticmethod(itemgetter('pokemon_id', 'form', 'levels'))

def reduce_encounters(root):
    # Here's what happens:
    # 1. We group by method (since different methods have different slots,
    #    encounters cannot reasonably be compared across methods).
    # 2. We group by terrain (since we can't collapse terrains).
    # 3. We group by slot. Each slot will be individually examined for
    #    reduction. We might collapse a condition (season, say) in slot 1, but
    #    not in slot 2. A condition like time or season can be collapsed if the
    #    encounter data for each of its values is identical. A higher condition,
    #    like swarm or slot2, can be collapsed if the data is identical *and*
    #    every lower condition can be collapsed.
    # 4. Once we figure out which conditions to keep, we take the cartesian
    #    product of the values of those conditions. This is the set of sets of
    #    condition values which will be represented in the database.
    # 5. For each set of condition values, the encounter data for the slot is
    #    computed under those conditions.
    # 6. Said data is added to the database.
    encounters_list = flatten_encounters(lift(root))
    for method, group in groupby(encounters_list, itemgetter('method')):
        for terrain, group in groupby(group, itemgetter('terrain')):
            for slot, encounters in groupby(group, itemgetter('slot')):
                encounters = list(encounters)
                #for e in encounters:
                #    print(e)
                monkey = EncounterMonkey(encounters)
                monkey.collapse_encounters()
                monkey.strip_redundancy()
                condition_values = \
                    [[(cond, value) for value in get_condition_values(cond)]
                     for cond in monkey.get_conditions()]

                #print(method, terrain, slot, monkey.encounters)

                for condition_set in itertools.product(*condition_values):
                    condition_set = dict(condition_set)
                    e = monkey.get_encounter(condition_set)
                    #print (condition_set, e)
                    if e:
                        e = e.copy()
                        e['conditions'] = condition_set
                        yield e
                    #else:
                    #    print (condition_set)

def flatten_encounters(encountergroups):
    flattened = []
    for group in encountergroups:
        context = {'conditions': {}}
        flattened.extend(_flatten(context, group))
    return flattened

def _flatten(context, group):
    context = context.copy()
    for key in ('method', 'terrain', 'rate'):
        if key in group:
            context[key] = group[key]

    if group['conditions']:
        c = context['conditions'].copy()
        c.update(group['conditions'])
        context['conditions'] = c

    for p in group['pokemon']:
        p['conditions'] = context['conditions'].copy()
        p['method'] = context['method']
        p['terrain'] = context.get('terrain')

        yield p

    for g in group['subgroups']:
        for p in _flatten(context, g):
            yield p

def insert_encounters(encounters, ctx):
    session.add_all(make_encounter(e, ctx) for e in encounters)

def make_encounter(obj, ctx):
    """Make an db.Encounter object from a dict"""

    slot = get_or_create_encounter_slot(
        slot = obj['slot'],
        version_group_id = ctx['version'].version_group_id,
        method = obj['method'],
        terrain = obj['terrain'],
    )

    e = Encounter()

    # Pokemon
    e.pokemon_id = obj['pokemon_id']
    #e.form_id = int(obj['form_id'])

    e.version_id = ctx['version'].id

    e.location_area = ctx['area']

    e.slot = slot

    # Add levels
    if len(obj['levels']) == 1:
        e.min_level = e.max_level = obj['levels'][0]
    elif len(obj['levels']) == 2:
        e.min_level, e.max_level = obj['levels']
    else:
        raise ValueError(obj['levels'])

    # Add conditions
    for cond_value in obj['conditions'].iteritems():
        c = get_condition(cond_value)
        e.condition_values.append(c)

    return e

def get_or_create_location(loc_elem, ctx):
    name = unicode(loc_elem.get('name'))
    q = session.query(Location).filter_by(
        name=name,
        region_id=ctx['region'].id,
    )
    try:
        loc = q.one()
    except (NoResultFound, MultipleResultsFound):
        loc = Location()
        loc.name = name
        loc.region = ctx['region']
        session.add(loc)
    return loc

_areas = {}
def create_area(area_elem, ctx):
    name = area_elem.get('name')
    if name is not None:
        name = unicode(name)

    key = (ctx['location'], name)
    if key in _areas:
        return _areas[key]

    area = LocationArea()
    area.name = name
    area.internal_id = int(area_elem.get('internal_id'))
    area.location = ctx['location']

    _areas[key] = area
    session.add(area)
    return area



def main():
    engine = create_engine('postgresql:///veekun-pokedex')

    session.bind = engine
    session.autoflush = False

    filename = sys.argv[1]

    xml = parse_xml(filename)

    ctx = {}
    for game in xml.xpath('/wild/game'):
        ctx['version'] = get_version(game.get('version'))
        # XXX region should be set based on the location
        ctx['region'] = ctx['version'].version_group.regions[0]
        for loc in game.xpath('location'):
            ctx['location'] = get_or_create_location(loc, ctx)
            for area in loc.xpath('area'):
                ctx['area'] = create_area(area, ctx)

                if area.get('name', False):
                    print loc.get('name') + "/" + area.get('name')
                else:
                    print loc.get('name')

                encounters = list(reduce_encounters(area))
                insert_encounters(encounters, ctx)
                #for e in sorted(encounters,
                #                key=itemgetter('method', 'terrain')):
                #    print e
            session.flush()
    session.commit()


if __name__ == '__main__':
    import time
    from sys import stdout, stderr
    time_a = time.time()
    main()
    time_b = time.time()
    stdout.flush()
    print >>stderr, "{:.4f} seconds".format(time_b - time_a)
