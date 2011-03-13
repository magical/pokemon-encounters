
import os
import os.path
import csv
from struct import unpack, pack
from collections import defaultdict

from lxml.etree import Element, SubElement, ElementTree

versions = ['firered', 'leafgreen']

def dump_xml(inf, outf, pretty_print=True):
    root = Element('wild')
    game = to_xml(inf, 'firered') # XXX
    root.append(game)
    outf.write("""<?xml version="1.0" encoding="utf-8"?>\n""")
    xml = ElementTree(root)

    xml.write(outf, pretty_print=pretty_print)

def to_xml(f, version):
    game = Element('game', version=version, language='en')

    class Locations(defaultdict):
        def __missing__(self, key):
            self[key] = value = SubElement(game, 'location', name=key)
            return value

    locations = Locations()

    records = parse_data(f)

    for i, record in enumerate(records):
        location_name, area_name = get_location_name(
            (record['bank'], record['num']))
        location = locations[location_name]
        area = SubElement(location, 'area',internal_id=str(i))
        if area_name:
            area.set('name', area_name)
        _do_monsters(area, record)

    return game

def _do_monsters(area, record):
    def fmtrange((a,b)):
        if a == b:
            return format(a, "d")
        else:
            return "{:d}-{:d}".format(a, b)

    def add_monsters(method, data):
        if not data:
            return
        monsters = SubElement(area, 'monsters',
            method=method, rate=str(data['rate']))

        for slot in data['slots']:
            SubElement(monsters, 'pokemon',
                number=str(slot['pokemon']),
                levels=fmtrange(slot['levels']),
                name=names[slot['pokemon']],
            )

    for method in ('walk', 'surf', 'rock-smash'):
        add_monsters(method, record['encounters'][method])

    fish = record['encounters']['fish']
    if fish:
        add_monsters('old-rod', {'rate': fish['rate'], 'slots': fish['slots'][0:2]})
        add_monsters('good-rod', {'rate': fish['rate'], 'slots': fish['slots'][2:5]})
        add_monsters('super-rod', {'rate': fish['rate'], 'slots': fish['slots'][5:10]})

def parse_data(f):
    while True:
        buf = f.read(2)
        if not buf:
            break

        bank, num = unpack("<BB", buf)
        flags = unpack("<????", f.read(4))

        def read_encounters(n, flag):
            if not flag:
                return None
            rate, = unpack("<H", f.read(2))
            slots = []
            for i in range(n):
                min_level, max_level, national_id = unpack("<BBH", f.read(4))
                slots.append({
                    'levels': (min_level, max_level),
                    'pokemon': national_id,
                })
            return {'rate': rate, 'slots': slots}

        record = {
            'bank': bank,
            'num': num,
            'encounters': {
                'walk': read_encounters(12, flags[0]),
                'surf': read_encounters(5, flags[1]),
                'rock-smash': read_encounters(5, flags[2]),
                'fish': read_encounters(10, flags[3]),
            },
        }

        yield record


def _load_names():
    global names
    if names is None:
        namefile = os.path.join(os.path.dirname(__file__), "../names.txt")
        names = open(namefile).read().splitlines()
        names = [x.decode('utf-8') for x in names]

def _load_locations():
    global locations
    if locations is None:
        locfile = os.path.join(os.path.dirname(__file__), "../frlg-locations.csv")
        f = open(locfile).read().splitlines()
        locations = {}
        for row in csv.DictReader(f):
            l = row['location'].decode('utf-8')
            a = row['area'].decode('utf-8')
            locations[int(row['bank']),int(row['num'])] = l, a

names = None
_load_names()

locations = None
_load_locations()



def get_location_name(location_id):
    if location_id in locations:
        return locations[location_id]
    else:
        bank, num = location_id
        return "FRLG Unknown", "Unknown Area {}:{}".format(bank, num)


