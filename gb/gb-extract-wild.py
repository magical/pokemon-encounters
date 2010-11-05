"""gb-extract-wild.py - extract wild encounter data from the GB Pokemon games

Supports the english verions of Red, Blue and Yellow.

This script is public domain.

Fuctions:

extract_data() - read data from a ROM and write it out in a more compact format
interpret_data() - read the extracted data and write it out in a human-parseable format

main() - calls extract_data() to convert *.gb files into wild-*.bin files in 
         the current directory.
         expects the ROMs to be in "../ROMs", because that's where they happen
         to be on my computer.

main2() - calls interpret_data() to convert wild-*.bin files into wild-*.txt
          files.


Variables:

pokemonNames - maps the national IDs of pokemon to their names
mapNat - maps internal IDs to national IDs

mapNamesVersions - names of the maps (loctions) for each game.
                   red and blue have the same maps, so i could probably do
                   with just a mapNames dict.


Compact Format:

a list of records. each record starts:
    byte - map number

then there are two encounter chunks, for grass and water encounters respectively
each chunk can be either 1 or 21 bytes long.
the first byte is the base encounter rate
    byte - base rate
if this value is zero, stop reading, the chunk is over.
otherwise, the ten encounter slots follow.
    byte - level
    byte - pokemon (national id)

keep reading until eof.


Appendix:

according to upokecenter.com, the rarities are
25% 15% 15% 10% 10% 10% 5% 5% 4% 1%

BUT THEY ARE WRONG.
i found this:
http://tasvideos.org/PokemonTricks.html
it explains the rng in some detail, and gives the encounter slot rates.
they are (guess what) out of 255 instead of 100.

here's the table:

====  =======  ==========  =======
Slot   Range   Percentage  Rounded
====  =======  ==========  =======
0       0-50   19.921875%    20%
1      51-101  19.921875%    20%
2     102-140  15.234375%    15%
3     141-165   9.765625%    10%
4     166-190   9.765625%    10%
5     191-215   9.765625%    10%
6     216-228   5.078125%     5%
7     229-241   5.078125%     5%
8     242-252   4.296875%     4%
9     253-255   1.171875%     1%
====  =======  ==========  =======

that is,
20 20 15 10 10 10 5 5 4 1
not
25 15 15 ...

"""


import os
from os import SEEK_SET
from struct import unpack, pack
import sys

#hackhackhack
reload(sys)
sys.setdefaultencoding("utf-8")

#pokemonNames, mapNamesVersions, and mapNat are defined at the end of the file

# I can't promise that these offsets will work for you
offsets = {
    'red': 0xCEB9,
    'blue': 0xCEB9,
    'yellow': 0xCB63,
}

#by the way:
#fishing data is at 0xe97d in red
#fishing data is at 0xf5eda in yellow

nodata = {
    'red': 0xd0dd,
    'blue': 0xd0dd,
    'yellow': 0xcd89,
}

versions = ['red', 'blue', 'yellow']

def main():
    for game in versions:
        infile = "../ROMs/%s.gb" % game
        outfile = "wild-%s.bin" % game
        if os.path.exists(infile):
            print game
            extract_data(game, infile, outfile)

def main2():
    for game in versions:
        infile = "wild-%s.bin" % game
        outfile = "wild-%s.txt" % game
        if os.path.exists(infile):
            print game
            interpret_data(game, infile, outfile)

def read_byte(f):
    s = f.read(1)
    assert len(s) == 1
    return unpack("<B", s)[0]

def read_short(f):
    s = f.read(2)
    assert len(s) == 2
    return unpack("<H", s)[0]

def read_adr(f, bank=3):
    i = read_short(f)
    if i == 0 or i == 0xffff:
        return None
    if i > 0x4000:
        i = i % 0x4000 + bank * 0x4000
    return i

def read_adr_and_jump(f):
    adr = read_adr(f)
    f.seek(adr, SEEK_SET)
    return adr

def read_encounter_data(rom):
    rate = read_byte(rom)
    if rate:
        l = [unpack("<BB", rom.read(2)) for _ in range(10)]
    else:
        l = []
    return rate, l

#http://twilight-hacking.darkbb.com/specific-questions-f22/red-wild-pokemon-headers-t137.htm
#http://www.datacrystal.org/wiki/Pokemon_Red/Blue:ROM_map

def extract_data(game, infile, outfile):
    """Read encounter data from a ROM, and save it in a more compact format.
    Also fixes the pokemon ID.
    """
    places = set()

    outfile = open(outfile, "wb")
    rom = open(infile, "rb")

    rom.seek(offsets[game])
    read_adr_and_jump(rom)

    def printit(rate, l):
        outfile.write(pack("<B", rate))
        if rate:
            for level, poke in l:
                try:
                    outfile.write(pack("<BB", level, mapNat[poke]))
                except KeyError:
                    print hex(here), poke, level, num, hex(p)
                    raise
        
    num = -1
    while True:
        num += 1
        p = read_adr(rom)
        if p is None:
            break

        # shortcut; points to an empty encounter list
        if p == nodata[game]:
            continue

        places.add(num)
        
        here = rom.tell()
        rom.seek(p, SEEK_SET)

        grass = read_encounter_data(rom)
        water = read_encounter_data(rom)
        if grass[0] or water[0]:
            outfile.write(pack("<B", num))
            printit(*grass)
            printit(*water)

        rom.seek(here, SEEK_SET)

    places = list(places)
    places.sort()
    for p in places:
        print "%d" % p
        
def interpret_data(game, infile, outfile):
    """Read in encounter data in the compact format, and output it as something resembling human-readable"""
    mapNames = mapNamesVersions[game]

    out = open(outfile, "w")
    data = open(infile, "rb")

    def printit(type, l):
        out.write("%s:%s:%s:" % (mapNames[num], type, rate))
        #out.write("%s:%s:%s:" % (num, type, rate))
        out.write(",". join("%s %d" % (pokemonNames[poke], level)
                             for level, poke in l))
        out.write("\n")
        
    def readnum():
        s = data.read(1)
        if len(s) < 1:
            return None
        return unpack("<B", s)[0]

    def read_encounters(count):
        return [ unpack("<BB", x)
                 for x in (data.read(2) for _ in xrange(count)) ]
    
    for num in iter(readnum, None):
        rate = read_byte(data)
        if rate:
            printit("grass", read_encounters(10))
        
        rate = read_byte(data)
        if rate:
            printit("water", read_encounters(10))


#########
## pokemonNames, mapNamesVersions, mapNat

pokemonNames = {
1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander", 5: "Charmeleon", 6: "Charizard", 7: "Squirtle", 8: "Wartortle", 9: "Blastoise", 10: "Caterpie", 11: "Metapod", 12: "Butterfree", 13: "Weedle", 14: "Kakuna", 15: "Beedrill", 16: "Pidgey", 17: "Pidgeotto", 18: "Pidgeot", 19: "Rattata", 20: "Raticate", 21: "Spearow", 22: "Fearow", 23: "Ekans", 24: "Arbok", 25: "Pikachu", 26: "Raichu", 27: "Sandshrew", 28: "Sandslash", 29: "Nidoran(f)", 30: "Nidorina", 31: "Nidoqueen", 32: "Nidoran(m)", 33: "Nidorino", 34: "Nidoking", 35: "Clefairy", 36: "Clefable", 37: "Vulpix", 38: "Ninetales", 39: "Jigglypuff", 40: "Wigglytuff", 41: "Zubat", 42: "Golbat", 43: "Oddish", 44: "Gloom", 45: "Vileplume", 46: "Paras", 47: "Parasect", 48: "Venonat", 49: "Venomoth", 50: "Diglett", 51: "Dugtrio", 52: "Meowth", 53: "Persian", 54: "Psyduck", 55: "Golduck", 56: "Mankey", 57: "Primeape", 58: "Growlithe", 59: "Arcanine", 60: "Poliwag", 61: "Poliwhirl", 62: "Poliwrath", 63: "Abra", 64: "Kadabra", 65: "Alakazam", 66: "Machop", 67: "Machoke", 68: "Machamp", 69: "Bellsprout", 70: "Weepinbell", 71: "Victreebel", 72: "Tentacool", 73: "Tentacruel", 74: "Geodude", 75: "Graveler", 76: "Golem", 77: "Ponyta", 78: "Rapidash", 79: "Slowpoke", 80: "Slowbro", 81: "Magnemite", 82: "Magneton", 83: "Farfetch\'d", 84: "Doduo", 85: "Dodrio", 86: "Seel", 87: "Dewgong", 88: "Grimer", 89: "Muk", 90: "Shellder", 91: "Cloyster", 92: "Gastly", 93: "Haunter", 94: "Gengar", 95: "Onix", 96: "Drowzee", 97: "Hypno", 98: "Krabby", 99: "Kingler", 100: "Voltorb", 101: "Electrode", 102: "Exeggcute", 103: "Exeggutor", 104: "Cubone", 105: "Marowak", 106: "Hitmonlee", 107: "Hitmonchan", 108: "Lickitung", 109: "Koffing", 110: "Weezing", 111: "Rhyhorn", 112: "Rhydon", 113: "Chansey", 114: "Tangela", 115: "Kangaskhan", 116: "Horsea", 117: "Seadra", 118: "Goldeen", 119: "Seaking", 120: "Staryu", 121: "Starmie", 122: "Mr.Mime", 123: "Scyther", 124: "Jynx", 125: "Electabuzz", 126: "Magmar", 127: "Pinsir", 128: "Tauros", 129: "Magikarp", 130: "Gyarados", 131: "Lapras", 132: "Ditto", 133: "Eevee", 134: "Vaporeon", 135: "Jolteon", 136: "Flareon", 137: "Porygon", 138: "Omanyte", 139: "Omastar", 140: "Kabuto", 141: "Kabutops", 142: "Aerodactyl", 143: "Snorlax", 144: "Articuno", 145: "Zapdos", 146: "Moltres", 147: "Dratini", 148: "Dragonair", 149: "Dragonite", 150: "Mewtwo", 151: "Mew",
}

mapNamesVersions = {
    'red': {
        12: "Route 1",
        13: "Route 2",
        14: "Route 3",
        15: "Route 4",
        16: "Route 5",
        17: "Route 6",
        18: "Route 7",
        19: "Route 8",
        20: "Route 9",
        21: "Route 10",
        22: "Route 11",
        23: "Route 12",
        24: "Route 13",
        25: "Route 14",
        26: "Route 15",
        27: "Route 16",
        28: "Route 17",
        29: "Route 18",
        30: "Sea Route 19",
        31: "Sea Route 20",
        32: "Sea Route 21",
        33: "Route 22",
        34: "Route 23",
        35: "Route 24",
        36: "Route 25",
        51: "Viridian Forest",
        59: "Mt. Moon/1F",
        60: "Mt. Moon/B1F",
        61: "Mt. Moon/B2F",
        82: "Rock Tunnel/BF1",
        83: "Power Plant",
        108: "Victory Road/1F",
        142: u"Pok\xe9mon Tower/1F",
        143: u"Pok\xe9mon Tower/2F",
        144: u"Pok\xe9mon Tower/3F",
        145: u"Pok\xe9mon Tower/4F",
        146: u"Pok\xe9mon Tower/5F",
        147: u"Pok\xe9mon Tower/6F",
        148: u"Pok\xe9mon Tower/7F",
        159: "Seafoam Islands/B1F", #2
        160: "Seafoam Islands/B2F", #3
        161: "Seafoam Islands/B3F", #4
        162: "Seafoam Islands/B4F", #5
        165: u"Pok\xe9mon Mansion/1F", #1
        192: "Seafoam Islands/1F", #1
        194: "Victory Road/2F",
        197: "DIGLETT's cave",
        198: "Victory Road/3F",
        214: u"Pok\xe9mon Mansion/2F", #2
        215: u"Pok\xe9mon Mansion/3F", #3
        216: u"Pok\xe9mon Mansion/B1F", #4
        217: "Safari Zone/Area 1, east",
        218: "Safari Zone/Area 2, north",
        219: "Safari Zone/Area 3, west",
        220: "Safari Zone/center area",
        226: "Cerulean Cave/2F",
        227: "Cerulean Cave/B1F",
        228: "Cerulean Cave/1F",
        232: "Rock Tunnel/BF2",
    }
}

mapNamesVersions['blue'] = mapNamesVersions['red']
mapNamesVersions['yellow'] = mapNamesVersions['red']


#http://twilight-hacking.darkbb.com/pokemon-generation-1-documents-f12/various-hex-lists-t4.htm
mapNat = {1: 112, 2: 115, 3: 32, 4: 35, 5: 21, 6: 100, 7: 34, 8: 80, 9: 2, 10: 103, 11: 108, 12: 102, 13: 88, 14: 94, 15: 29, 16: 31, 17: 104, 18: 111, 19: 131, 20: 59, 21: 151, 22: 130, 23: 90, 24: 72, 25: 92, 26: 123, 27: 120, 28: 9, 29: 127, 30: 114, 33: 58, 34: 95, 35: 22, 36: 16, 37: 79, 38: 64, 39: 75, 40: 113, 41: 67, 42: 122, 43: 106, 44: 107, 45: 24, 46: 47, 47: 54, 48: 96, 49: 76, 51: 126, 53: 125, 54: 82, 55: 109, 57: 56, 58: 86, 59: 50, 60: 128, 64: 83, 65: 48, 66: 149, 70: 84, 71: 60, 72: 124, 73: 146, 74: 144, 75: 145, 76: 132, 77: 52, 78: 98, 82: 37, 83: 38, 84: 25, 85: 26, 88: 147, 89: 148, 90: 140, 91: 141, 92: 116, 93: 117, 96: 27, 97: 28, 98: 138, 99: 139, 100: 39, 101: 40, 102: 133, 103: 136, 104: 135, 105: 134, 106: 66, 107: 41, 108: 23, 109: 46, 110: 61, 111: 62, 112: 13, 113: 14, 114: 15, 116: 85, 117: 57, 118: 51, 119: 49, 120: 87, 123: 10, 124: 11, 125: 12, 126: 68, 128: 55, 129: 97, 130: 42, 131: 150, 132: 143, 133: 129, 136: 89, 138: 99, 139: 91, 141: 101, 142: 36, 143: 110, 144: 53, 145: 105, 147: 93, 148: 63, 149: 65, 150: 17, 151: 18, 152: 121, 153: 1, 154: 3, 155: 73, 157: 118, 158: 119, 163: 77, 164: 78, 165: 19, 166: 20, 167: 33, 168: 30, 169: 74, 170: 137, 171: 142, 173: 81, 176: 4, 177: 7, 178: 5, 179: 8, 180: 6, 185: 43, 186: 44, 187: 45, 188: 69, 189: 70, 190: 71}

#########

#main()
main2()
