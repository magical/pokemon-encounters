#!/usr/bin/env python
# encoding: utf8
"""Takes the output of:

    porigon-z game.nds cat --format=hex \\
        /fielddata/encountdata/hg_enc_data.narc

and converts it to SQL queries for loading into the `pokedex` database.

This expects to be run after the equivalent D/P/Pt script.  Again, only meant
to be run twice.
"""

VERSION_ID = 16
VERSION_GROUP_ID = 9  # don't change this one!
SINNOH_AREA_CT = 183
SINNOH_LOCATION_CT = 64

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

def words_to_bytes(words):
    bytes = []
    for word in words:
        bytes.append(word & 0xff)
        bytes.append(word >> 8)
    return bytes

# XXX:
# - need to set internal ids for every location area..
# - times for the ToD would be nice
def main():
    location_area_id = SINNOH_AREA_CT
    for line in sys.stdin:
        location_area_id += 1

        nybbles = list(line.strip())
        words = []

        # Convert list of nybbles (0 .. f) to list of words (16-bit ints)
        # (What a pain in the ass.  Why isn't this dead simple?)
        for word_nybble in ichunk(nybbles, 8):
            word = 0

            #    a b c d e f g h
            # => hg, fe, dc, ba
            # => gh fe cd ab
            for byte in ichunk(reversed(word_nybble), 2):
                word *= 256
                word += int(''.join(reversed(byte)), 16)

            words.append(word & 0xffff)
            words.append(word >> 16)

        location, area = [(loc, area) for (idx, loc, area) in location_areas() if idx == location_area_id - SINNOH_AREA_CT][0]
        print '--', location_area_id, location, area
        print '--', words

        # OK, do data fuckery.
        rates = words_to_bytes(better_pop(words, 4))
        rate_terrains = [1, 5, 6, 2, 3, 4]
        if VERSION_ID == 15:
            for rate, terrain_id in zip(rates, rate_terrains):
                if not rate or not terrain_id:
                    continue
                print """INSERT INTO location_area_encounter_rates VALUES ({location_area_id}, {encounter_terrain_id}, {rate});""" \
                      .format(location_area_id=location_area_id, encounter_terrain_id=terrain_id, rate=rate)

        INSERT_ENCOUNTER = partial(
            """INSERT INTO encounters VALUES (DEFAULT, {version_id}, {area_id}, {slot_id}, {pokemon_id}, {min_level}, {max_level});""".format,
            version_id=VERSION_ID, area_id=location_area_id
        )
        ADD_CONDITION = """INSERT INTO encounter_condition_value_map VALUES (currval('encounters_id_seq'), {0});""".format

        ### Grass encounters
        levels = words_to_bytes(better_pop(words, 6))
        morn = better_pop(words, 12)
        day = better_pop(words, 12)
        night = better_pop(words, 12)

        hoenn_radio = better_pop(words, 2)
        sinnoh_radio = better_pop(words, 2)

        surfing = list( ichunk(better_pop(words, 10), 2) )
        rock_smash = list( ichunk(better_pop(words, 4), 2) )
        old_rod = list( ichunk(better_pop(words, 10), 2) )
        good_rod = list( ichunk(better_pop(words, 10), 2) )
        super_rod = list( ichunk(better_pop(words, 10), 2) )
        swarm = better_pop(words, 4)

        # Same sort of thing as with D/P, except all twelve slots have time of day
        # [ (slot_num, [default_conds], [ (pokemon, cond_value_id), ... ]), ... ]
        alternates_map = [
            ( 1, [2], [(swarm[0], 1)] ),
            ( 2, [2], [(swarm[0], 1)] ),
            ( 3, [14], [(hoenn_radio[0], 15), (sinnoh_radio[0], 16)] ),
            ( 4, [14], [(hoenn_radio[0], 15), (sinnoh_radio[0], 16)] ),
            ( 5, [14], [(hoenn_radio[1], 15), (sinnoh_radio[1], 16)] ),
            ( 6, [14], [(hoenn_radio[1], 15), (sinnoh_radio[1], 16)] ),
            ( 7, [], [] ),
            ( 8, [], [] ),
            ( 9, [], [] ),
            (10, [], [] ),
            (11, [], [] ),
            (12, [], [] ),
        ]
        for slot_id, level in enumerate(levels):
            if morn[slot_id] == 0:
                # No walking in this area, apparently
                continue

            slot_num, defaults, alt_data = alternates_map[slot_id]
            slot_num += 32

            # Okay, we have two levels of stuff going on here.
            # FIRST, time-of-day may or may not be collapsed into one row.
            # THEN, only IF those are the same, the alternates might be
            # collapsable too.  Either way, alts aren't affected by whatever
            # happens with time of day.
            collapse_time = False
            collapse_all = False

            if morn[slot_id] == day[slot_id] and day[slot_id] == night[slot_id]:
                collapse_time = True

            alts = [pokemon for (pokemon, _) in alt_data]
            if collapse_time and len(set( [morn[slot_id]] + alts )) == 1:
                print "-- COLLAPSING ALL FOR SLOT {0}".format(slot_num)
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=morn[slot_id], min_level=level, max_level=level)
                continue

            if collapse_time:
                print "-- COLLAPSING TIME FOR SLOT {0}".format(slot_num)
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=morn[slot_id], min_level=level, max_level=level)

                for default_cond_id in defaults:
                    print ADD_CONDITION(default_cond_id)

            else:
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=morn[slot_id], min_level=level, max_level=level)
                for default_cond_id in defaults + [3]:
                    print ADD_CONDITION(default_cond_id)
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=day[slot_id], min_level=level, max_level=level)
                for default_cond_id in defaults + [4]:
                    print ADD_CONDITION(default_cond_id)
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=night[slot_id], min_level=level, max_level=level)
                for default_cond_id in defaults + [5]:
                    print ADD_CONDITION(default_cond_id)


            # Add alternates..
            for pokemon, cond_id in alt_data:
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=pokemon, min_level=level, max_level=level)
                print ADD_CONDITION(cond_id)

        ### Rock Smash
        for i, (level_blob, pokemon) in enumerate(rock_smash):
            if not pokemon:
                continue
            max_level = level_blob & 0xff
            min_level = level_blob >> 8
            print INSERT_ENCOUNTER(slot_id=65 + i, pokemon_id=pokemon, min_level=min_level, max_level=max_level)

        ### Water
        # First some setup to see if all the possible swarm-fish slots contain
        # the same Pokémon.  Iff they do, it's possible there's no swarm at all
        swarming_fish = set([  # (terrain, slot)
            (2, 2),
            (3, 0),
            (3, 2),
            (3, 3),
            (4, 0),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 4),
        ])
        fish_terrain = {
            2: old_rod,
            3: good_rod,
            4: super_rod,
        }
        swarm_fish_pokemon = None
        swarm_fish_pokemon_set = set(
            fish_terrain[terrain_id][slot_id]
            for (terrain_id, slot_id)
            in swarming_fish
        )
        if len(swarm_fish_pokemon_set) == 1:
            swarm_fish_pokemon, = swarm_fish_pokemon_set

        for terrain_id, encounters in [
            (5, surfing),
            (2, old_rod),
            (3, good_rod),
            (4, super_rod),
        ]:
            if not terrain_id or not encounters[0][1]:
                # Skip filler and places without water
                continue

            for slot_id, (level_blob, pokemon) in enumerate(encounters):
                slot_num = 45 + 5 * (terrain_id - 2) + slot_id
                max_level = level_blob & 0xff
                min_level = level_blob >> 8
                print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=pokemon, min_level=min_level, max_level=max_level)

                # Surfing swarm
                if terrain_id == 5 and slot_id == 0 and swarm[1] != pokemon:
                    print ADD_CONDITION(17)
                    print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=swarm[1], min_level=min_level, max_level=max_level)
                    print ADD_CONDITION(18)

                # Fishing swarm
                if (terrain_id, slot_id) in swarming_fish and (swarm_fish_pokemon != swarm[3] or swarm_fish_pokemon != swarm[2]):
                    print ADD_CONDITION(19)
                    print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=swarm[3], min_level=min_level, max_level=max_level)
                    print ADD_CONDITION(20)
                    print INSERT_ENCOUNTER(slot_id=slot_num, pokemon_id=swarm[2], min_level=min_level, max_level=max_level)
                    print ADD_CONDITION(21)

        print
        # XXX add terrain_id to conditions


def load_environment():
    # Locations and areas
    current_location = None
    current_location_id = SINNOH_LOCATION_CT
    for idx, location, area in location_areas():
        if location != current_location:
            # New location: load it up
            current_location_id += 1
            current_location = location
            print """INSERT INTO locations (id, generation_id, name) VALUES ({location_id}, 4, $${name}$$);""" \
                  .format(location_id=current_location_id, name=current_location)

        print """INSERT INTO location_areas (id, location_id, internal_id, name) VALUES ({area_id}, {location_id}, {internal_id}, {name});""" \
              .format(area_id=idx + SINNOH_AREA_CT, location_id=current_location_id, internal_id=idx, name='$${0}$$'.format(area) if area else 'NULL')

    # Terrain -- suitable for every version, ever!  I think
    #for id, name in [
    #    (1, 'Walking in tall grass or a cave'),
    #    (2, 'Fishing with an Old Rod'),
    #    (3, 'Fishing with a Good Rod'),
    #    (4, 'Fishing with a Super Rod'),
    #    (5, 'Surfing'),
    #    (6, 'Smashing rocks'),
    #    (7, 'Headbutting trees'),
    # XXX headbutt is separate, still.  :(
    #]:
    #    print """INSERT INTO encounter_terrain (id, name) VALUES ({id}, $${name}$$);""" \
    #          .format(id=id, name=name)

    # Slots
    for slot_num, terrain_id, rarity in [
        # Walking
        #( 1, 1, 20),
        #( 2, 1, 20),
        #( 3, 1, 10),
        #( 4, 1, 10),
        #( 5, 1, 10),
        #( 6, 1, 10),
        #( 7, 1,  5),
        #( 8, 1,  5),
        #( 9, 1,  4),
        #(10, 1,  4),
        #(11, 1,  1),
        #(12, 1,  1),
        # Fishing and surfing
        #(13, 2, 60),
        #(14, 2, 30),
        #(15, 2,  5),
        #(16, 2,  4),
        #(17, 2,  1),
        #(18, 3, 60),
        #(19, 3, 30),
        #(20, 3,  5),
        #(21, 3,  4),
        #(22, 3,  1),
        #(23, 4, 60),
        #(24, 4, 30),
        #(25, 4,  5),
        #(26, 4,  4),
        #(27, 4,  1),
        #(28, 5, 60),
        #(29, 5, 30),
        #(30, 5,  5),
        #(31, 5,  4),
        #(32, 5,  1),
        ### HGSS edition
        # Walking
        (33, 1, 20),
        (34, 1, 20),
        (35, 1, 10),
        (36, 1, 10),
        (37, 1, 10),
        (38, 1, 10),
        (39, 1,  5),
        (40, 1,  5),
        (41, 1,  4),
        (42, 1,  4),
        (43, 1,  1),
        (44, 1,  1),
        # Fishing and surfing
        (45, 2, 60),
        (46, 2, 30),
        (47, 2,  5),
        (48, 2,  4),
        (49, 2,  1),
        (50, 3, 60),
        (51, 3, 30),
        (52, 3,  5),
        (53, 3,  4),
        (54, 3,  1),
        (55, 4, 60),
        (56, 4, 30),
        (57, 4,  5),
        (58, 4,  4),
        (59, 4,  1),
        (60, 5, 60),
        (61, 5, 30),
        (62, 5,  5),
        (63, 5,  4),
        (64, 5,  1),
        # Rock Smash
        (65, 6, 90),
        (66, 6, 10),
    ]:
        print """INSERT INTO encounter_slots (id, encounter_terrain_id, rarity, version_group_id) VALUES ({slot_id}, {terrain_id}, {rarity}, {version_group_id});""" \
              .format(slot_id=slot_num, terrain_id=terrain_id, rarity=rarity, version_group_id=VERSION_GROUP_ID)

    # Conditions
    for id, name in [
        #(1, 'Swarm'),
        #(2, 'Time of day'),
        #(3, u'PokeRadar'),
        #(4, 'Gen 3 game in slot 2'),
        (5, 'Radio'),
        (6, 'Surfing swarm'),
        (7, 'Fishing swarm'),
    ]:
        print u"""INSERT INTO encounter_conditions VALUES ({id}, $${name}$$);""" \
              .format(id=id, name=name)

    # Slot conditions
    for slot_id, cond_id in [
        # Grass; time of day and swarms
        (33, 2),
        (33, 1),
        (34, 2),
        (34, 1),
        (35, 2),
        (35, 5),
        (36, 2),
        (36, 5),
        (37, 2),
        (37, 5),
        (38, 2),
        (38, 5),
        (39, 2),
        (40, 2),
        (41, 2),
        (42, 2),
        (43, 2),
        (44, 2),
        # Fish fish fish surf
        (47, 7),
        (50, 7),
        (52, 7),
        (53, 7),
        (55, 7),
        (56, 7),
        (57, 7),
        (58, 7),
        (59, 7),
        (60, 6),
    ]:
        print u"""INSERT INTO encounter_slot_conditions VALUES ({0}, {1});""" \
              .format(slot_id, cond_id)

    for id, cond_id, default, name in [
        #( 1, 1, False, 'During a swarm'),
        #( 2, 1, True,  'Not during a swarm'),
        #( 3, 2, False, 'In the morning'),
        #( 4, 2, True,  'During the day'),
        #( 5, 2, False, 'At night'),
        #( 6, 3, False, u'Using PokeRadar'),
        #( 7, 3, True,  u'Not using PokeRadar'),
        #( 8, 4, True, 'No game in slot 2'),
        #( 9, 4, False, 'Ruby in slot 2'),
        #(10, 4, False, 'Sapphire in slot 2'),
        #(11, 4, False, 'Emerald in slot 2'),
        #(12, 4, False, 'Fire Red in slot 2'),
        #(13, 4, False, 'Leaf Green in slot 2'),
        (14, 5, True,  'Radio off'),
        (15, 5, False, 'Hoenn radio'),
        (16, 5, False, 'Sinnoh radio'),
        (17, 6, True,  'No surfing swarm'),
        (18, 6, False, 'Surfing swarm'),
        (19, 7, True,  'No fishing swarm'),
        (20, 7, False, 'Fishing swarm'),
        (21, 7, False, 'Fishing swarm 2?'),
    ]:
        print u"""INSERT INTO encounter_condition_values VALUES ({id}, {cond_id}, $${name}$$, {default});""" \
              .format(id=id, cond_id=cond_id, name=name, default='true' if default else 'false')


def location_areas():
    return [
        (66, 'Blackthorn City', ''),
        (29, 'Burned Tower', '1F'),
        (30, 'Burned Tower', 'B1F'),
        (100, 'Celadon City', ''),
        (98, 'Cerulean City', ''),
        (3, 'Cherrygrove City', ''),
        (52, 'Cianwood City', ''),
        (96, 'Cinnabar Island', ''),
        (71, 'Dark Cave', 'Blackthorn City entrance'),
        (70, 'Dark Cave', 'Violet City entrance'),
        (134, 'Diglett\'s Cave', ''),
        (67, 'Dragon\'s Den', ''),
        (28, 'Ecruteak City', ''),
        (101, 'Fuchsia City', ''),
        (61, 'Ice Cave', '1F'),
        (62, 'Ice Cave', 'B1F'),
        (63, 'Ice Cave', 'B2F'),
        (64, 'Ice Cave', 'B3F'),
        (21, 'Ilex Forest', ''),
        (59, 'Lake of Rage', ''),
        (107, 'Mt. Moon', '1F'),
        (108, 'Mt. Moon', '2F'),
        (73, 'Mt. Moon', 'outside'),
        (54, 'Mt. Mortar', '1F'),
        (57, 'Mt. Mortar', 'B1F'),
        (55, 'Mt. Mortar', 'Lower Cave'),
        (56, 'Mt. Mortar', 'Upper Cave'),
        (81, 'Mt. Silver', '1F top'),
        (80, 'Mt. Silver', '1F'),
        (87, 'Mt. Silver', '2F'),
        (89, 'Mt. Silver', '3F'),
        (82, 'Mt. Silver', '4F'),
        (88, 'Mt. Silver', 'mountainside'),
        (86, 'Mt. Silver', 'outside'),
        (90, 'Mt. Silver', 'top'),
        (24, 'National Park', ''),
        (1, 'New Bark Town', ''),
        (41, 'Olivine City', ''),
        (102, 'Pallet Town', ''),
        (109, 'Rock Tunnel', '1F'),
        (110, 'Rock Tunnel', 'B1F'),
        (112, 'Route 1', ''),
        (121, 'Route 10', ''),
        (122, 'Route 11', ''),
        (93, 'Route 12', ''),
        (123, 'Route 13', ''),
        (124, 'Route 14', ''),
        (125, 'Route 15', ''),
        (126, 'Route 16', ''),
        (127, 'Route 17', ''),
        (128, 'Route 18', ''),
        (94, 'Route 19', ''),
        (113, 'Route 2', ''),
        (137, 'Route 2', 'something else'),
        (95, 'Route 20', ''),
        (129, 'Route 21', ''),
        (130, 'Route 22', ''),
        (131, 'Route 24', ''),
        (132, 'Route 25', ''),
        (104, 'Route 26', ''),
        (105, 'Route 27', ''),
        (106, 'Route 28', ''),
        (2, 'Route 29', ''),
        (114, 'Route 3', ''),
        (4, 'Route 30', ''),
        (5, 'Route 31', ''),
        (9, 'Route 32', ''),
        (18, 'Route 33', ''),
        (22, 'Route 34', ''),
        (23, 'Route 35', ''),
        (26, 'Route 36', ''),
        (27, 'Route 37', ''),
        (39, 'Route 38', ''),
        (40, 'Route 39', ''),
        (115, 'Route 4', ''),
        (42, 'Route 40', ''),
        (43, 'Route 41', ''),
        (53, 'Route 42', ''),
        (58, 'Route 43', ''),
        (60, 'Route 44', ''),
        (68, 'Route 45', ''),
        (69, 'Route 46', ''),
        (72, 'Route 47', ''),
        (83, 'Route 47', 'cave gate'),
        (84, 'Route 47', 'inside cave'),
        (103, 'Route 48', ''),
        (116, 'Route 5', ''),
        (117, 'Route 6', ''),
        (118, 'Route 7', ''),
        (119, 'Route 8', ''),
        (120, 'Route 9', ''),
        (11, 'Ruins of Alph', 'Interior A'),
        (12, 'Ruins of Alph', 'Interior B'),
        (13, 'Ruins of Alph', 'Interior C'),
        (14, 'Ruins of Alph', 'Interior D'),
        (10, 'Ruins of Alph', 'Outside'),
        (75, 'Seafoam Islands', '1F'),
        (76, 'Seafoam Islands', 'B1F'),
        (77, 'Seafoam Islands', 'B2F'),
        (78, 'Seafoam Islands', 'B3F'),
        (79, 'Seafoam Islands', 'B4F'),
        (19, 'Slowpoke Well', '1F'),
        (20, 'Slowpoke Well', 'B1F'),
        (7, 'Sprout Tower', '2F'),
        (8, 'Sprout Tower', '3F'),
        (85, 'Tin Tower', '10F'),
        (31, 'Tin Tower', '2F'),
        (32, 'Tin Tower', '3F'),
        (33, 'Tin Tower', '4F'),
        (34, 'Tin Tower', '5F'),
        (35, 'Tin Tower', '6F'),
        (36, 'Tin Tower', '7F'),
        (37, 'Tin Tower', '8F'),
        (38, 'Tin Tower', '9F'),
        (133, 'Tohjo Falls', ''),
        (15, 'Union Cave', '1F'),
        (16, 'Union Cave', 'B1F'),
        (17, 'Union Cave', 'B2F'),
        (139, 'Unknown 138', ''),
        (50, 'Unknown 49', ''),
        (51, 'Unknown 50', ''),
        (65, 'Unknown 64', ''),
        (91, 'Unknown 90', ''),
        (140, 'Unknown Dungeon', '1F'),
        (141, 'Unknown Dungeon', '2F'),
        (142, 'Unknown Dungeon', 'B1F'),
        (74, 'Unknown; all Poliwag', ''),
        (92, 'Unknown; all Rattata', ''),
        (25, 'Unknown; all bugs', ''),
        (99, 'Vermilion City', ''),
        (111, 'Victory Road', ''),
        (135, 'Victory Road', 'one'),
        (136, 'Victory Road', 'two'),
        (6, 'Violet City', ''),
        (97, 'Viridian City', ''),
        (138, 'Viridian Forest', ''),
        (49, 'Whirl Islands', 'B3F'),
        (46, 'Whirl Islands', 'empty floor X'),
        (48, 'Whirl Islands', 'empty floor Y'),
        (44, 'Whirl Islands', 'unknown floors A'),
        (45, 'Whirl Islands', 'unknown floors B'),
        (47, 'Whirl Islands', 'unknown floors C'),
    ]


if VERSION_ID == 15:
    # Load the prereqs, like locations and slots
    load_environment()
main()
