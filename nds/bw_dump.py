from cStringIO import StringIO
from struct import pack, unpack

from .narc import parse_narc


seasons = ('spring', 'summer', 'autumn', 'winter')

def chunkit(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def dump_csv(narc_file, csv_writer):
    records = parse_narc(narc_file)
    writerow = csv_writer.writerow

    for i, record in enumerate(records):
        if 292 < len(record):
            for season, subrecord in zip(seasons, chunkit(record, 292)):
                _dump_record(writerow, i, season, record)
        else:
            _dump_record(writerow, i, None, record)

def _dump_record(writerow, location, season, record):
    pass

####

def dump_text(narc_file, out):
    load_names()
    records = parse_narc(narc_file)

    def write(*args, **kw):
        sep = kw.pop('sep', " ")
        end = kw.pop('end', "\n")
        out.write(sep.join(str(x) for x in args))
        out.write(end)

    for i, record in enumerate(records):
        write("Location", i)
        if len(record) > 232:
            for season, subrecord in zip(seasons, chunkit(record, 232)):
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
        return [unpack("<HBB", x) for x in chunkit(chunk.read(4*n), 4)]

    def writeencounters(prefix, list, predicate, kidding=False):
        if not predicate or kidding:
            return
        #if bool(list[0][0]) == bool(predicate):
        #    return   

        write(prefix, end=" ")
        text = []
        for pok, minl, maxl in list:
            form = pok >> 11
            pok = pok & 0x07ff
            name = "#" + str(pok)
            try:
                name += " " + names[pok]
            except IndexError:
                pass
            text.append("Lv.%s %s" % (fmtrange(minl, maxl), name))
            if form or pok in (550, 585, 586):
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


names = None
def load_names():
    global names
    if names is None:
        import os.path
        namefile = os.path.join(os.path.dirname(__file__), "../names.txt")
        names = open(namefile).read().splitlines()
