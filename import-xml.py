#!/usr/bin/env python2

from __future__ import unicode_literals

import sys
import itertools
from copy import deepcopy
from operator import itemgetter
from lxml.etree import parse as parse_xml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from db import Encounter, EncounterCondition, EncounterConditionValue
from db import EncounterMethod, EncounterTerrain, EncounterSlot
from db import Location, LocationArea
from db import Version

SessionClass = sessionmaker()

# globals! oh noes!
session = SessionClass()

_conditions = {}
_condition_values = {}
def load_conditions():
    q = (session.query(EncounterConditionValue,
                       EncounterCondition.identifier)
            .join(EncounterCondition)
            .order_by(EncounterCondition.id, EncounterConditionValue.id))
    for cond_value_obj, cond in q.all():
        cond_value = cond_value_obj.identifier
        _conditions[cond, cond_value] = cond_value_obj
        if cond not in _condition_values:
            _condition_values[cond] = []
        _condition_values[cond].append(cond_value)

def get_condition(cond, value):
    return _conditions[unicode(cond), unicode(value)]

def get_condition_values(cond):
    return _condition_values[unicode(cond)]

_versions = {}
def load_versions():
    q = session.query(Version)
    for version in q.all():
        _versions[version.name.lower()] = version

def get_version(version):
    return _versions[unicode(version)]

def encounter_add_condition(self, cond, value):
    self.condition_values.append(get_condition(cond, value))

def parse_range(s):
    min, _, max = s.partition('-')
    min = int(min)
    if max:
        max = int(max)
        return min, max
    else:
        return min, min

def lift_conditions(e):
    all_conditions = set(a for a, b in _conditions)
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

    return obj

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
        for cond in ('season', 'time'):
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
            ['spots'],
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

def insert_encounters(session, ctx, encounters):
    for e in encounters:
        encounter = make_encounter(e, ctx)
        session.add(encounter)
    session.flush()

def make_encounter(obj, ctx):
    """Make an db.Encounter object from a dict"""

    #XXX not very efficient
    def get_terrain_id(terrain):
        return session.query(EncounterTerrain.id).filter_by(identifier=terrain).one()[0]
    def get_method_id(method):
        return session.query(EncounterMethod.id).filter_by(identifier=method).one()[0]
    def get_or_create_encounter_slot(slot, method_id, version_group_id,
                                     terrain_id=None):
        q = session.query(EncounterSlot).filter_by(
            slot=slot,
            version_group_id=version_group_id,
            encounter_method_id=method_id,
            encounter_terrain_id=terrain_id,
        )
        try:
            x = q.one()
        except NoResultFound:
            x = EncounterSlot()
            x.slot=slot
            x.version_group_id=version_group_id
            x.encounter_method_id=method_id
            x.encounter_terrain_id=terrain_id
        return x

    e = Encounter()

    # Pokemon
    e.pokemon_id = obj['pokemon_id']
    #e.form_id = int(obj['form_id'])

    e.version_id = ctx['version'].id

    if obj['terrain'] is not None:
        terrain_id = get_terrain_id(obj['terrain'])
    else:
        terrain_id = None
    method_id = get_method_id(obj['method'])

    e.slot = get_or_create_encounter_slot(
        slot = obj['slot'],
        version_group_id = ctx['version'].version_group_id,
        method_id = method_id,
        terrain_id = terrain_id,
    )

    e.location_area = ctx['area']

    # Add levels
    if len(obj['levels']) == 1:
        e.min_level = e.max_level = obj['levels'][0]
    elif len(obj['levels']) == 2:
        e.min_level, e.max_level = obj['levels']
    else:
        raise ValueError(obj['levels'])

    # Add conditions
    for cond, value in obj['conditions'].iteritems():
        c = get_condition(cond, value)
        e.condition_values.append(c)
    return e

def get_or_create_location(session, loc_elem, ctx):
    q = session.query(Location).filter_by(
        name=loc_elem.get('name'),
        region_id=ctx['region'].id,
    )
    try:
        loc = q.one()
    except NoResultFound:
        loc = Location()
        loc.name = loc_elem.get('name')
        loc.region = ctx['region']
        session.add(loc)
    return loc

def create_area(session, area_elem, ctx):
    area = LocationArea()
    area.name = area_elem.get('name')
    area.internal_id = int(area_elem.get('internal_id'))
    area.location = ctx['location']
    session.add(area)
    return area



def main():
    engine = create_engine('sqlite:///test.sqlite')
    session.bind = engine

    load_conditions()
    load_versions()

    with open(sys.argv[1], "rb") as f:
        # Although the documentation for lxml discourages passing 
        # unicode, that seem to be the only way to get it to use
        # unicode strings in the tree.
        xml = parse_xml(f)

    ctx = {}
    for game in xml.xpath('/wild/game'):
        ctx['version'] = get_version(game.get('version'))
        # XXX
        ctx['region'] = ctx['version'].version_group.generation.main_region
        for loc in game.xpath('location'):
            ctx['location'] = get_or_create_location(session, loc, ctx)
            for area in loc.xpath('area'):
                ctx['area'] = create_area(session, area, ctx)

                if area.get('name', ''):
                    print loc.get('name') + "/" + area.get('name')
                else:
                    print loc.get('name')

                encounters = reduce_encounters(area)
                insert_encounters(session, ctx, encounters)
                #for e in sorted(encounters,
                #                key=itemgetter('method', 'terrain')):
                #    print e
    session.commit()


if __name__ == '__main__':
    import time
    from sys import stdout, stderr
    time_a = time.time()
    main()
    time_b = time.time()
    stdout.flush()
    print >>stderr, "{:.4f} seconds".format(time_b - time_a)
