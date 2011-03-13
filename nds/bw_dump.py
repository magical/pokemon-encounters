from cStringIO import StringIO
from struct import pack, unpack
from lxml.etree import ElementTree, Element, SubElement
from collections import defaultdict
from itertools import groupby
from operator import itemgetter

from .narc import parse_narc


SEASONS = ('spring', 'summer', 'autumn', 'winter')
FORMS = {
    550: ('red-striped', 'blue-striped'),
    585: SEASONS,
    586: SEASONS,
}


def chunkit(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def _unpack_entry(entry):
    pokemon, min_level, max_level = unpack("<HBB", entry)
    return pokemon, (min_level, max_level)

def _readencounters(f, n):
    return map(_unpack_entry, chunkit(f.read(4*n), 4))


def dump_csv(narc_file, csv_writer):
    records = parse_narc(narc_file)
    writerow = csv_writer.writerow

    for i, record in enumerate(records):
        if 232 < len(record):
            for season, subrecord in zip(SEASONS, chunkit(record, 232)):
                _dump_record(writerow, i, season, record)
        else:
            _dump_record(writerow, i, None, record)

def _dump_record(writerow, location, season, record):
    pass

####

def dump_text(narc_file, out):
    records = parse_narc(narc_file)

    def write(*args, **kw):
        sep = kw.pop('sep', " ")
        end = kw.pop('end', "\n")
        out.write(sep.join(unicode(x).encode('utf-8') for x in args))
        out.write(end)

    for i, record in enumerate(records):
        location, area = get_location_name(i)
        if area:
            name = u"{}/{}".format(location,area)
        else:
            name = location
        write(u"{}: {}".format(i, name))
        #write("Location", i)
        if len(record) > 232:
            for season, subrecord in zip(SEASONS, chunkit(record, 232)):
                write(" {}:".format(season.capitalize()))
                _dumpencounter(write, subrecord)
        else:
            _dumpencounter(write, record)

def fmtrange(min, max):
    if min == max:
        return str(min)
    else:
        return "{}-{}".format(min, max)

def _dumpencounter(write, chunk):
    chunk = StringIO(chunk)

    def readencounters(n):
        return _readencounters(chunk, n)

    def writeencounters(prefix, list, predicate, kidding=False):
        if not predicate or kidding:
            return
        #if bool(list[0][0]) == bool(predicate):
        #    return   

        write(prefix, end=" ")
        text = []
        for pok, levels in list:
            form = pok >> 11
            pok = pok & 0x07ff
            name = "#" + str(pok)
            try:
                name += " " + names[pok]
            except IndexError:
                pass
            text.append("Lv.%s %s" % (fmtrange(*levels), name))
            if pok in (550, 585, 586):
                text[-1] += " Form#%s" % form
            else:
                assert form == 0

        write(', '.join(text))

    rates = map(ord, chunk.read(8))
    encounter_type = rates.pop()

    write("  Rates:", rates)
    write("  encounter type:", encounter_type)
    write()
    if encounter_type == 0:
        writeencounters("  Grass:    ", readencounters(12), rates[0])
    elif encounter_type == 1:
        writeencounters("  Cave:     ", readencounters(12), rates[0])
    elif encounter_type == 2:
        write(          "  Bridge:   ")
        writeencounters("", readencounters(12), rates[0])
    else:
        raise ValueError(encounter_type)

    writeencounters("  - Doubles:", readencounters(12), rates[1])
    writeencounters("  - Special:", readencounters(12), rates[2])
    writeencounters("  Surf:     ", readencounters(5), rates[3])
    writeencounters("  - Special:", readencounters(5), rates[4])
    writeencounters("  Fish:     ", readencounters(5), rates[5])
    writeencounters("  - Special:", readencounters(5), rates[6])
    write()


#####

def dump_xml(narc_file, out):
    xml = to_xml(narc_file)
    xml.write(out, pretty_print=True, encoding="utf-8", xml_declaration=True)

def to_xml(narc_file):
    root = Element('wild')
    game = SubElement(root, 'game', version='black') # XXX

    def unpack_entry(entry):
        pokemon, min_level, max_level = unpack("<HBB", entry)
        return pokemon, (min_level, max_level)

    def readencounters(n):
        return map(unpack_entry, chunkit(chunk.read(4*n), 4))

    class Locations(defaultdict):
        def __missing__(self, key):
            self[key] = value = SubElement(game, 'location', name=key)
            return value
    locations = Locations()
    areas = {}

    records = parse_narc(narc_file)

    for location_id, record in enumerate(records):
        location_name, area_name = get_location_name(location_id)

        location = locations[location_name]
        area = SubElement(location, 'area', name=area_name,
                                            internal_id=str(location_id))

        if 232 < len(record):
            for season, subrecord in zip(SEASONS, chunkit(record, 232)):
                m = Element('monsters', season=season)
                _dump_xml_record(m, subrecord)
                if len(m):
                    area.append(m)
        else:
            _dump_xml_record(area, record)

    return ElementTree(root)

def _dump_xml_record(parent, record):
    record = StringIO(record)

    rates = map(ord, record.read(8))
    encounter_type = rates.pop()

    grass = _readencounters(record, 12)
    doubles = _readencounters(record, 12)
    grass_special = _readencounters(record, 12)

    water = _readencounters(record, 5)
    water_special = _readencounters(record, 5)

    fishing = _readencounters(record, 5)
    fishing_special = _readencounters(record, 5)

    def something(method, terrain, spots, encounters, rate):
        if not rate:
            return
        monsters = SubElement(parent, 'monsters',
            method=method,
        )
        if not spots:
            monsters.set('rate', str(rate))
        if terrain:
            monsters.set('terrain', terrain)
        if spots:
            monsters.set('spots', 'spots')
        for slot, (poke, levels) in enumerate(encounters):
            poke, form_index = poke & 0x7ff, poke >> 11
            e = SubElement(monsters, 'pokemon',
                number=str(poke),
                levels=fmtrange(*levels),
                name=names[poke],
                #slot=str(slot),
            )
            if poke in FORMS:
                form = FORMS[poke][form_index]
                e.set('form', str(form))
            else:
                assert form_index == 0, (poke, form_index)

    assert not (rates[1] and encounter_type != 0), (
        "doubles grass in non-grass area")

    walk_terrain = 'grass'
    if encounter_type == 1:
        walk_terrain = 'cave'
    elif encounter_type == 2:
        walk_terrain = 'bridge'

    something('walk', walk_terrain, '',      grass,         rates[0])
    something('walk', walk_terrain, 'spots', grass_special, rates[2])
    something('walk', 'dark-grass', '',      doubles,       rates[1])

    something('surf', '', '',      water,         rates[3])
    something('surf', '', 'spots', water_special, rates[4])

    something('fish', '', '',      fishing,         rates[5])
    something('fish', '', 'spots', fishing_special, rates[6])


names = None
def load_names():
    global names
    if names is None:
        import os.path
        namefile = os.path.join(os.path.dirname(__file__), "../names.txt")
        names = open(namefile).read().splitlines()

locations = None
def load_locations():
    global locations
    if locations is None:
        import os.path, csv
        locfile = os.path.join(os.path.dirname(__file__), "../bw-locations-redux.csv")
        f = open(locfile).read().splitlines()
        locations = {}
        key = itemgetter('location')
        rows = sorted(csv.DictReader(f), key=key)
        for location, area_rows in groupby(rows, key):
            area_rows = list(area_rows)
            if len(area_rows) == 1 and area_rows[0]['area'] == "":
                row = area_rows[0]
                locations[int(row['id'])] = row['location'].decode('utf-8'), row['area']
            else:
                for row in area_rows:
                    locations[int(row['id'])] = (
                        row['location'].decode('utf-8'),
                        row['area'] or "Unknown Area {}".format(row['id']),
                    )

load_names()
load_locations()

def get_location_name(location_id):
    if location_id in locations:
        return locations[location_id]
    else:
        return "BW Unknown", "Unknown Area {}".format(location_id)
