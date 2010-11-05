#!/usr/bin/env python
# encoding: utf8
"""Takes the output of:

    porigon-z game.nds cat --format=hex \\
        /fielddata/encountdata/d_enc_data.narc

and converts it to SQL queries for loading into the `pokedex` database.  This
includes loading the location names, their sub-areas, terrain, and slots -- and
all of these things have pre-assigned ids, so they won't appreciate being
loaded into anything but a fresh table.  Luckily, this is only done if
`VERSION_ID` is set to 12, for Diamond.  Unluckily, this means you have to
change `VERSION_ID` to match the game you're loading.  Sorry; this was really
only meant to be run once.  Er, thrice.
"""

VERSION_ID = 12
VERSION_GROUP_ID = 8  # don't change this one!

from functools import partial
import sys

def better_pop(array, x):
    ret = array[0:x]
    array[0:x] = []
    return ret

def ichunk(it, n):
    ch = ()
    for item in it:
        ch += (item,)
        if len(ch) == n:
            yield ch
            ch = ()

# XXX:
# - need to set internal ids for every location area..
# - times for the ToD would be nice
def main():
    location_area_id = 0
    for line in sys.stdin:
        location_area_id += 1

        nybbles = list(line.strip())
        words = []

        # Convert list of nybbles (0 .. f) to list of words (32-bit ints)
        # (What a pain in the ass.  Why isn't this dead simple?)
        for word_nybble in ichunk(nybbles, 8):
            word = 0

            #    a b c d e f g h
            # => hg, fe, dc, ba
            # => gh fe cd ab
            for byte in ichunk(reversed(word_nybble), 2):
                word *= 256
                word += int(''.join(reversed(byte)), 16)

            words.append(word)


        print '--', location_area_id, location_areas()[location_area_id - 1]
        # OK, do data fuckery.
        rate = words.pop(0)
        if rate and VERSION_ID == 12:
            print """INSERT INTO location_area_encounter_rates VALUES ({location_area_id}, {encounter_terrain_id}, {rate});""" \
                  .format(location_area_id=location_area_id, encounter_terrain_id=1, rate=rate)

        INSERT_ENCOUNTER = partial(
            """INSERT INTO encounters VALUES (DEFAULT, {version_id}, {area_id}, {slot_id}, {pokemon_id}, {min_level}, {max_level});""".format,
            version_id=VERSION_ID, area_id=location_area_id
        )

        ### Grass encounters
        grass = list( ichunk(better_pop(words, 24), 2) )  # [ (lv, poke), ... ]

        ### Grass special encounters
        alts1 = better_pop(words, 10)  # swarm, day, night, pokeradar
        filler = better_pop(words, 6)  # XXX still don't know what this is..
        alts2 = better_pop(words, 10)  # r, s, e, fr, lg
        alts = alts1 + alts2

        # Okay.  Ten of the twelve grass slots have replacement Pokémon under
        # certain conditions, for a total of 20 replacements.  IFF none of the
        # replacements for a slot are any different than the original Pokémon,
        # then there's no reason to fill in new rows and conditions, and we can
        # simply do nothing.  HOWEVER, if ANY of them are different, then we
        # need to add a condition row for the original slot AND encounters +
        # conditions for each of the replacements.  Got that?  All or nothin.

        # First we need a map of grass slots to their alt slots and what
        # condition values they represent.
        # [ (slot_num, [default_conds], [ (alt_id, cond_value_id), ... ]), ... ]
        alternates_map = [
            ( 1, [2], [(0, 1)] ),  # swarm
            ( 2, [2], [(1, 1)] ),  # swarm
            ( 3, [3], [(2, 4), (4, 5)] ),  # day, night
            ( 4, [3], [(3, 4), (5, 5)] ),  # day, night
            ( 5, [7], [(6, 6)] ),  # poketore
            ( 6, [7], [(7, 6)] ),  # poketore
            ( 7, [], [] ),  # nothin
            ( 8, [], [] ),  # nothin
            ( 9, [8], [(10, 9), (12, 10), (14, 11), (16, 12), (18, 13)] ),  # various gba games
            (10, [8], [(11, 9), (13, 10), (15, 11), (17, 12), (19, 13)] ),  # various gba games
            (11, [7], [(8, 6)] ),  # poketore
            (12, [7], [(9, 6)] ),  # poketore
        ]
        for slot_id, (level, pokemon) in enumerate(grass):
            if pokemon == 0:
                # No walking in this area, apparently
                continue

            slot_num, defaults, alt_data = alternates_map[slot_id]

            print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=pokemon, min_level=level, max_level=level)

            # Compare the original Pokémon and the alternates, and see if any
            # of them are different.  If not, then we don't need to do anything
            # here; there's only one row and it has no condition values
            # attached
            slot_alts = [alts[alt_idx] for (alt_idx, _) in alt_data]
            if len(set( [pokemon] + slot_alts )) == 1:
                print "-- SKIPPING ALTERNATES FOR SLOT {0}".format(slot_num)
                continue

            # Okay, now we know we have to add a condition value for the
            # existing encounter, then encounters and condition values for all
            # the alternates
            for default_cond_id in defaults:
                print """INSERT INTO encounter_condition_value_map VALUES (currval('encounters_id_seq'), {0});""".format(default_cond_id)

            for alt_idx, cond_id in alt_data:
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=alts[alt_idx], min_level=level, max_level=level)
                print """INSERT INTO encounter_condition_value_map VALUES (currval('encounters_id_seq'), {0});""".format(cond_id)

        ### That just leaves water, which has no conditions!  Hurrah.
        for terrain_id in [5, None, 2, 3, 4]:  # surfing, filler, old/good/super rods
            rate = words.pop(0)
            encounters = list( ichunk(better_pop(words, 10), 2) )

            if not terrain_id or not rate:
                # Skip filler and places without water
                continue

            if VERSION_ID == 12:
                print """INSERT INTO location_area_encounter_rates VALUES ({location_area_id}, {encounter_terrain_id}, {rate});""" \
                      .format(location_area_id=location_area_id, encounter_terrain_id=terrain_id, rate=rate)

            for slot_id, (level_blob, pokemon) in enumerate(encounters):
                slot_num = 13 + 5 * (terrain_id - 2) + slot_id
                max_level = level_blob & 0xff
                min_level = level_blob >> 8
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=pokemon, min_level=min_level, max_level=max_level)

        print


def load_environment():
    # Locations and areas
    current_location = None
    current_location_id = 0
    for idx, (location, area) in enumerate(location_areas()):
        if location != current_location:
            # New location: load it up
            current_location_id += 1
            current_location = location
            print """INSERT INTO locations (id, generation_id, name) VALUES ({location_id}, 4, $${name}$$);""" \
                  .format(location_id=current_location_id, name=current_location)

        print """INSERT INTO location_areas (id, location_id, internal_id, name) VALUES ({area_id}, {location_id}, {internal_id}, {name});""" \
              .format(area_id=idx + 1, location_id=current_location_id, internal_id=idx + 1, name='$${0}$$'.format(area) if area else 'NULL')

    # Terrain -- suitable for every version, ever!  I think
    for id, name in [
        (1, 'Walking in tall grass or a cave'),
        (2, 'Fishing with an Old Rod'),
        (3, 'Fishing with a Good Rod'),
        (4, 'Fishing with a Super Rod'),
        (5, 'Surfing'),
        (6, 'Smashing rocks'),
        (7, 'Headbutting trees'),
    ]:
        print """INSERT INTO encounter_terrain (id, name) VALUES ({id}, $${name}$$);""" \
              .format(id=id, name=name)

    # Slots
    for slot_num, terrain_id, rarity in [
        # Walking
        ( 1, 1, 20),
        ( 2, 1, 20),
        ( 3, 1, 10),
        ( 4, 1, 10),
        ( 5, 1, 10),
        ( 6, 1, 10),
        ( 7, 1,  5),
        ( 8, 1,  5),
        ( 9, 1,  4),
        (10, 1,  4),
        (11, 1,  1),
        (12, 1,  1),
        # Fishing and surfing
        (13, 2, 60),
        (14, 2, 30),
        (15, 2,  5),
        (16, 2,  4),
        (17, 2,  1),
        (18, 3, 60),
        (19, 3, 30),
        (20, 3,  5),
        (21, 3,  4),
        (22, 3,  1),
        (23, 4, 60),
        (24, 4, 30),
        (25, 4,  5),
        (26, 4,  4),
        (27, 4,  1),
        (28, 5, 60),
        (29, 5, 30),
        (30, 5,  5),
        (31, 5,  4),
        (32, 5,  1),
    ]:
        print """INSERT INTO encounter_slots (id, encounter_terrain_id, rarity, version_group_id) VALUES ({slot_id}, {terrain_id}, {rarity}, {version_group_id});""" \
              .format(slot_id=slot_num, terrain_id=terrain_id, rarity=rarity, version_group_id=VERSION_GROUP_ID)

    # Conditions
    for id, name in [
        (1, 'Swarm'),
        (2, 'Time of day'),
        (3, u'PokeRadar'),
        (4, 'Gen 3 game in slot 2'),
    ]:
        print u"""INSERT INTO encounter_conditions VALUES ({id}, $${name}$$);""" \
              .format(id=id, name=name)

    # Slot conditions
    for slot_id, cond_id in [
        (1, 1),
        (2, 1),
        (3, 2),
        (4, 2),
        (5, 3),
        (6, 3),
        (9, 4),
        (10, 4),
        (11, 3),
        (12, 3),
    ]:
        print u"""INSERT INTO encounter_slot_conditions VALUES ({0}, {1});""" \
              .format(slot_id, cond_id)

    for id, cond_id, default, name in [
        ( 1, 1, False, 'During a swarm'),
        ( 2, 1, True,  'Not during a swarm'),
        ( 3, 2, False, 'In the morning'),
        ( 4, 2, True,  'During the day'),
        ( 5, 2, False, 'At night'),
        ( 6, 3, False, u'Using PokeRadar'),
        ( 7, 3, True,  u'Not using PokeRadar'),
        ( 8, 4, True, 'No game in slot 2'),
        ( 9, 4, False, 'Ruby in slot 2'),
        (10, 4, False, 'Sapphire in slot 2'),
        (11, 4, False, 'Emerald in slot 2'),
        (12, 4, False, 'Fire Red in slot 2'),
        (13, 4, False, 'Leaf Green in slot 2'),
    ]:
        print u"""INSERT INTO encounter_condition_values VALUES ({id}, {cond_id}, $${name}$$, {default});""" \
              .format(id=id, cond_id=cond_id, name=name, default='true' if default else 'false')


def location_areas():
    return [
        ("Canalave City",""),
        ("Eterna City",""),
        ("Pastoria City",""),
        ("Sunyshore City",""),
        ("Pokemon League",""),
        ("Oreburgh Mine", "1F"),
        ("Oreburgh Mine", "B1F"),
        ("Valley Windworks",""),
        ("Eterna Forest",""),
        ("Fuego Ironworks",""),
        ("Mt. Coronet", "Route 207"),
        ("Mt. Coronet", "2F"),
        ("Mt. Coronet", "3F"),
        ("Mt. Coronet", "snowfall"),
        ("Mt. Coronet", "blizzard"),
        ("Mt. Coronet", "4F"),
        ("Mt. Coronet", "5F"),
        ("Mt. Coronet", "6F"),
        ("Mt. Coronet", "7F"),
        ("Mt. Coronet", "cave"),
        ("Mt. Coronet", "Route 216"),
        ("Mt. Coronet", "Route 211"),
        ("Mt. Coronet", "B1F"),
        ("Safari Zone", "Area 1"),
        ("Safari Zone", "Area 2"),
        ("Safari Zone", "Area 3"),
        ("Safari Zone", "Area 4"),
        ("Safari Zone", "Area 5"),
        ("Safari Zone", "Area 6"),
        ("Solaceon Ruins", "2F"),
        ("Solaceon Ruins", "1F"),
        ("Solaceon Ruins", "B1F a"),
        ("Solaceon Ruins", "B1F b"),
        ("Solaceon Ruins", "B1F c"),
        ("Solaceon Ruins", "B2F a"),
        ("Solaceon Ruins", "B2F b"),
        ("Solaceon Ruins", "B2F c"),
        ("Solaceon Ruins", "B3F a"),
        ("Solaceon Ruins", "B3F b"),
        ("Solaceon Ruins", "B3F c"),
        ("Solaceon Ruins", "B3F d"),
        ("Solaceon Ruins", "B3F e"),
        ("Solaceon Ruins", "B4F a"),
        ("Solaceon Ruins", "B4F b"),
        ("Solaceon Ruins", "B4F c"),
        ("Solaceon Ruins", "B4F d"),
        ("Solaceon Ruins", "B5F"),
        ("Victory Road", "1F"),
        ("Victory Road", "2F"),
        ("Victory Road", "B1F"),
        ("Victory Road", "inside B1F"),
        ("Victory Road", "inside"),
        ("Victory Road", "inside exit"),
        ("Deserted Escape Path",""),
        ("Oreburgh Tunnel", "1F"),
        ("Oreburgh Tunnel", "B1F"),
        ("Stark Mountain",""),
        ("Stark Mountain", "entrance"),
        ("Stark Mountain", "inside"),
        ("Spring Path",""),
        ("Turnback Cave", "a"),
        ("Turnback Cave", "b"),
        ("Turnback Cave", "c"),
        ("Turnback Cave", "d"),
        ("Turnback Cave", "e"),
        ("Turnback Cave", "f"),
        ("Turnback Cave", "g"),
        ("Turnback Cave", "h"),
        ("Turnback Cave", "i"),
        ("Turnback Cave", "j"),
        ("Turnback Cave", "k"),
        ("Turnback Cave", "l"),
        ("Turnback Cave", "m"),
        ("Turnback Cave", "n"),
        ("Turnback Cave", "o"),
        ("Turnback Cave", "p"),
        ("Turnback Cave", "q"),
        ("Turnback Cave", "r"),
        ("Turnback Cave", "s"),
        ("Turnback Cave", "t"),
        ("Turnback Cave", "u"),
        ("Turnback Cave", "v"),
        ("Turnback Cave", "w"),
        ("Turnback Cave", "x"),
        ("Turnback Cave", "y"),
        ("Turnback Cave", "z"),
        ("Turnback Cave", "alpha"),
        ("Turnback Cave", "beta"),
        ("Turnback Cave", "gamma"),
        ("Turnback Cave", "delta"),
        ("Turnback Cave", "epsilon"),
        ("Turnback Cave", "zeta"),
        ("Turnback Cave", "eta"),
        ("Turnback Cave", "theta"),
        ("Turnback Cave", "iota"),
        ("Turnback Cave", "kappa"),
        ("Turnback Cave", "lambda"),
        ("Turnback Cave", "mu"),
        ("Turnback Cave", "nu"),
        ("Turnback Cave", "xi"),
        ("Turnback Cave", "omicron"),
        ("Turnback Cave", "pi"),
        ("Turnback Cave", "rho"),
        ("Turnback Cave", "sigma"),
        ("Turnback Cave", "tau"),
        ("Turnback Cave", "upsilon"),
        ("Snowpoint Temple", "1F"),
        ("Snowpoint Temple", "B1F"),
        ("Snowpoint Temple", "B2F"),
        ("Snowpoint Temple", "B3F"),
        ("Snowpoint Temple", "B4F"),
        ("Snowpoint Temple", "B5F"),
        ("Wayward Cave", "1F"),
        ("Wayward Cave", "B1F"),
        ("Ruins Maniac's Cave",""),
        ("Ruins Maniac's Cave", "expansion"),
        ("Ruins Maniac's Tunnel",""),
        ("Pokemon Mansion garden",""),
        ("Iron Island",""),
        ("Iron Island", "1F"),
        ("Iron Island", "B1F left"),
        ("Iron Island", "B1F right"),
        ("Iron Island", "B2F right"),
        ("Iron Island", "B2F left"),
        ("Iron Island", "B3F"),
        ("Old Chateau", "entrance"),
        ("Old Chateau", "dining room"),
        ("Old Chateau", "2F private room"),
        ("Old Chateau", "2F"),
        ("Old Chateau", "2F leftmost room"),
        ("Old Chateau", "2F left room"),
        ("Old Chateau", "2F middle room"),
        ("Old Chateau", "2F right room"),
        ("Old Chateau", "2F rightmost room"),
        ("Lake Verity", "before"),
        ("Lake Verity", "after"),
        ("Lake Valour",""),
        ("Lake Acuity",""),
        ("Near Lake Valour",""),
        ("Near Lake Acuity",""),
        ("Route 201",""),
        ("Route 202",""),
        ("Route 203",""),
        ("Route 204", "Jubilife City side"),
        ("Route 204", "Floaroma City side"),
        ("Route 205", "Floaroma City side"),
        ("Route 205", "Eterna City side"),
        ("Route 206",""),
        ("Route 207",""),
        ("Route 208",""),
        ("Route 209",""),
        ("Lost Tower", "1F"),
        ("Lost Tower", "2F"),
        ("Lost Tower", "3F"),
        ("Lost Tower", "4F"),
        ("Lost Tower", "5F"),
        ("Route 210", "Solaceon City side"),
        ("Route 210", "Celestic City side"),
        ("Route 211", "Eterna City side"),
        ("Route 211", "Celestic City side"),
        ("Route 212", "Hearthome City side"),
        ("Route 212", "Pastoria City side"),
        ("Route 213",""),
        ("Route 214",""),
        ("Route 215",""),
        ("Route 216",""),
        ("Route 217",""),
        ("Route 218",""),
        ("Route 219",""),
        ("Route 221",""),
        ("Route 222",""),
        ("Route 224",""),
        ("Route 225",""),
        ("Route 227",""),
        ("Route 228",""),
        ("Route 229",""),
        ("Twinleaf Town",""),
        ("Celestic City",""),
        ("Resort Area",""),
        ("Sea Route 220",""),
        ("Sea Route 223",""),
        ("Sea Route 226",""),
        ("Sea Route 230",""),
    ]


if VERSION_ID == 12:
    # Load the prereqs, like locations and slots
    load_environment()
main()
