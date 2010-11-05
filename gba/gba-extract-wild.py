"""gba-extract-wild.py - extract wild encounter data from the GBA Pokemon games

Fuctions:

extract_data() - read data from a ROM and write it out in a more compact format
interpret_data() - read the extracted data and write it out in a human-parseable format

main() - calls extract_data() to convert *.gba files into wild-*.bin files in 
         the current directory.
         expects the ROMs to be in a subdirectory called "ROMs", because
         that's where they are for me.

main2() - calls interpret_data() to convert wild-*.bin files into wild-*.txt
          files.


Variables:

pokemonNames - maps the internal IDs of pokemon to their names
mapNat - maps internal IDs to national IDs, where they differ

mapNamesVersions - names of the maps (loctions). arranged by game->bank->map


Compact Format:

a list of records. each record starts:
    byte - bank number
    byte - map number
together these identify the location.
then, four booleans
    byte - grass?
    byte - water?
    byte - rocks?
    byte - fish?

these indicate which types of encounter data are stored.
then there are 1-4 blocks of encounter data, per the booleans.
each block starts:
    short - rate
which is the rate at which wild pokemon appear.

then you have a number of slots, depending on the type of encounter.
grass uses 12 slots; water 5; rocks 5; and fish has 10: 
2, 3, and 5 slots each for the old, good, and super rods.

each slot is arranged as so:
    byte - min level
    byte - max level
    short - national id of pokemon

there you have it. just keep reading until you reach the end of the file.


Appendix:

here are what i believe the rarities are for each slot, based on information
i found around the internet.

Grass: 20 20 10 10 10 10 5 5 4 4 1 1
Rock Smash: 60 30 5 4 1
Surfing: 60 30 5 4 1
Fishing:
    Old Rod: 70 30
    Good Rod: 60 20 20
    Super Rod: 40 40 15 4 1

"""


import os
from os import SEEK_SET
from struct import unpack, pack
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

#pokemonNames, mapNamesVersions, and mapNat are defined at the end of the file

# I can't promise that these offsets will work for you
#START = 0x084aa4
offsets = {
    'emerald': 0x0b5560,
    'ruby': 0x0852e4,
    'sapphire': 0x0852e4,
    'firered': 0x082ea8,
    'leafgreen': 0x082e7c,
}

versions = ['ruby', 'sapphire', 'firered', 'leafgreen', 'emerald']

def main():
    for game in versions:
        infile = "ROMs/%s.gba" % game
        outfile = "wild-%s.bin" % game
        if os.path.exists(infile):
            print game
            extract_data(game, infile, outfile)

def main2():
    fix_pokemonNames()
    for game in versions:
        infile = "wild-%s.bin" % game
        outfile = "wild-%s.txt" % game
        if os.path.exists(infile):
            print game
            interpret_data(game, infile, outfile)

def read_long(f):
    s = f.read(4)
    assert len(s) == 4
    return unpack("<L", s)[0]

def read_adr(f):
    i = read_long(f)
    if i == 0:
        return None
    assert i >> 24 == 0x08
    return i & 0xffffff

def read_adr_and_jump(f):
    adr = read_adr(f)
    f.seek(adr, SEEK_SET)
    return adr

def read_encounter_data(rom, adr, count):
    rom.seek(adr, SEEK_SET)
    rate = read_long(rom)
    read_adr_and_jump(rom)
    l = []
    for i in range(count):
        #lmin, lmax, poke
        l.append(unpack("<BBH", rom.read(4)))
    return rate, l



def extract_data(game, infile, outfile):
    """Read encounter data from a ROM, and save it in a more compact format.
    Also fixes the pokemon ID.
    """
    places = set()

    outfile = open(outfile, "wb")
    rom = open(infile, "rb")

    rom.seek(offsets[game])
    read_adr_and_jump(rom)

    def printit():
        outfile.write(pack("<H", rate))
        for lmin, lmax, poke in l:
            outfile.write(pack("<BBH", lmin, lmax, mapNat.get(poke, poke)))
        
    while True:
        #bank = ord(rom.read(1))
        #if bank == 0xff:
        #    break
        #num = ord(rom.read(1))
        #rom.read(2)
        bank, num = unpack("<BBxx", rom.read(4))
        if bank == 0xff:
            break

        places.add((bank, num))

        grass = read_adr(rom)
        water = read_adr(rom)
        rocks = read_adr(rom)
        fishy = read_adr(rom)

        outfile.write(pack("<BB", bank, num))
        outfile.write(pack("<????", grass, water, rocks, fishy))
        here = rom.tell()

        if grass:
            rate, l = read_encounter_data(rom, grass, 12)
            printit()
        if water:
            rate, l = read_encounter_data(rom, water, 5)
            printit()
        if rocks:
            rate, l = read_encounter_data(rom, rocks, 5)
            printit()
        if fishy:
            rate, l = read_encounter_data(rom, fishy, 10)
            printit()

        rom.seek(here, SEEK_SET)

    places = list(places)
    places.sort()
    for p in places:
        print "%d.%d" % p
        
def fix_pokemonNames():
    global pokemonNames
    pokemonNames = dict((mapNat.get(n, n), p) for n, p in pokemonNames.iteritems())

def interpret_data(game, infile, outfile):
    """Read in encounter data in the compact format, and output it as something resembling human-readable"""
    mapNames = mapNamesVersions[game]

    out = open(outfile, "w")
    data = open(infile, "rb")

    def printit(type, l):
        out.write("%s:%s:%s:" % (mapNames[bank][num], type, rate))
        out.write(",". join("%s %d-%d" % (pokemonNames[poke], lmin, lmax)
                             for lmin, lmax, poke in l))
        out.write("\n")
        
    def readbank():
        s = data.read(2)
        if len(s) < 2:
            return None
        return unpack("<BB", s)

    def read_encounters(count):
        return [ unpack("<BBH", _) 
                 for _ in (data.read(4) for _ in xrange(count)) ]
    
    for bank, num in iter(readbank, None):
        grass, water, rocks, fishy = unpack("<????", data.read(4))

        if grass:
            rate = unpack("<H", data.read(2))[0]
            l = read_encounters(12)
            printit("grass", l)
        if water:
            rate = unpack("<H", data.read(2))[0]
            l = read_encounters(5)
            printit("water", l)
        if rocks:
            rate = unpack("<H", data.read(2))[0]
            l = read_encounters(5)
            printit("rocks", l)
        if fishy:
            rate = unpack("<H", data.read(2))[0]
            old, good, super = map(read_encounters, [2, 3, 5])
            printit("old rod", old)
            printit("good rod", good)
            printit("super rod", super)

##rarities
## Grass: 20 20 10 10 10 10 5 5 4 4 1 1
## Rock Smash: 60 30 5 4 1
## Surfing: 60 30 5 4 1
## Fishing:
##    Old Rod: 70 30
##    Good Rod: 60 20 20
##    Super Rod: 40 40 15 4 1


#########
## pokemonNames, mapNamesVersions, mapNat

pokemonNames = {
1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander", 5: "Charmeleon", 6: "Charizard", 7: "Squirtle", 8: "Wartortle", 9: "Blastoise", 10: "Caterpie", 11: "Metapod", 12: "Butterfree", 13: "Weedle", 14: "Kakuna", 15: "Beedrill", 16: "Pidgey", 17: "Pidgeotto", 18: "Pidgeot", 19: "Rattata", 20: "Raticate", 21: "Spearow", 22: "Fearow", 23: "Ekans", 24: "Arbok", 25: "Pikachu", 26: "Raichu", 27: "Sandshrew", 28: "Sandslash", 29: "Nidoran(f)", 30: "Nidorina", 31: "Nidoqueen", 32: "Nidoran(m)", 33: "Nidorino", 34: "Nidoking", 35: "Clefairy", 36: "Clefable", 37: "Vulpix", 38: "Ninetales", 39: "Jigglypuff", 40: "Wigglytuff", 41: "Zubat", 42: "Golbat", 43: "Oddish", 44: "Gloom", 45: "Vileplume", 46: "Paras", 47: "Parasect", 48: "Venonat", 49: "Venomoth", 50: "Diglett", 51: "Dugtrio", 52: "Meowth", 53: "Persian", 54: "Psyduck", 55: "Golduck", 56: "Mankey", 57: "Primeape", 58: "Growlithe", 59: "Arcanine", 60: "Poliwag", 61: "Poliwhirl", 62: "Poliwrath", 63: "Abra", 64: "Kadabra", 65: "Alakazam", 66: "Machop", 67: "Machoke", 68: "Machamp", 69: "Bellsprout", 70: "Weepinbell", 71: "Victreebel", 72: "Tentacool", 73: "Tentacruel", 74: "Geodude", 75: "Graveler", 76: "Golem", 77: "Ponyta", 78: "Rapidash", 79: "Slowpoke", 80: "Slowbro", 81: "Magnemite", 82: "Magneton", 83: "Farfetch\'d", 84: "Doduo", 85: "Dodrio", 86: "Seel", 87: "Dewgong", 88: "Grimer", 89: "Muk", 90: "Shellder", 91: "Cloyster", 92: "Gastly", 93: "Haunter", 94: "Gengar", 95: "Onix", 96: "Drowzee", 97: "Hypno", 98: "Krabby", 99: "Kingler", 100: "Voltorb", 101: "Electrode", 102: "Exeggcute", 103: "Exeggutor", 104: "Cubone", 105: "Marowak", 106: "Hitmonlee", 107: "Hitmonchan", 108: "Lickitung", 109: "Koffing", 110: "Weezing", 111: "Rhyhorn", 112: "Rhydon", 113: "Chansey", 114: "Tangela", 115: "Kangaskhan", 116: "Horsea", 117: "Seadra", 118: "Goldeen", 119: "Seaking", 120: "Staryu", 121: "Starmie", 122: "Mr.Mime", 123: "Scyther", 124: "Jynx", 125: "Electabuzz", 126: "Magmar", 127: "Pinsir", 128: "Tauros", 129: "Magikarp", 130: "Gyarados", 131: "Lapras", 132: "Ditto", 133: "Eevee", 134: "Vaporeon", 135: "Jolteon", 136: "Flareon", 137: "Porygon", 138: "Omanyte", 139: "Omastar", 140: "Kabuto", 141: "Kabutops", 142: "Aerodactyl", 143: "Snorlax", 144: "Articuno", 145: "Zapdos", 146: "Moltres", 147: "Dratini", 148: "Dragonair", 149: "Dragonite", 150: "Mewtwo", 151: "Mew",
152: "Chikorita", 153: "Bayleef", 154: "Meganium", 155: "Cyndaquil", 156: "Quilava", 157: "Typhlosion", 158: "Totodile", 159: "Croconaw", 160: "Feraligatr", 161: "Sentret", 162: "Furret", 163: "Hoothoot", 164: "Noctowl", 165: "Ledyba", 166: "Ledian", 167: "Spinarak", 168: "Ariados", 169: "Crobat", 170: "Chinchou", 171: "Lanturn", 172: "Pichu", 173: "Cleffa", 174: "Igglybuff", 175: "Togepi", 176: "Togetic", 177: "Natu", 178: "Xatu", 179: "Mareep", 180: "Flaaffy", 181: "Ampharos", 182: "Bellossom", 183: "Marill", 184: "Azumarill", 185: "Sudowoodo", 186: "Politoed", 187: "Hoppip", 188: "Skiploom", 189: "Jumpluff", 190: "Aipom", 191: "Sunkern", 192: "Sunflora", 193: "Yanma", 194: "Wooper", 195: "Quagsire", 196: "Espeon", 197: "Umbreon", 198: "Murkrow", 199: "Slowking", 200: "Misdreavus", 201: "Unown", 202: "Wobbuffet", 203: "Girafarig", 204: "Pineco", 205: "Forretress", 206: "Dunsparce", 207: "Gligar", 208: "Steelix", 209: "Snubbull", 210: "Granbull", 211: "Qwilfish", 212: "Scizor", 213: "Shuckle", 214: "Heracross", 215: "Sneasel", 216: "Teddiursa", 217: "Ursaring", 218: "Slugma", 219: "Magcargo", 220: "Swinub", 221: "Piloswine", 222: "Corsola", 223: "Remoraid", 224: "Octillery", 225: "Delibird", 226: "Mantine", 227: "Skarmory", 228: "Houndour", 229: "Houndoom", 230: "Kingdra", 231: "Phanpy", 232: "Donphan", 233: "Porygon2", 234: "Stantler", 235: "Smeargle", 236: "Tyrogue", 237: "Hitmontop", 238: "Smoochum", 239: "Elekid", 240: "Magby", 241: "Miltank", 242: "Blissey", 243: "Raikou", 244: "Entei", 245: "Suicune", 246: "Larvitar", 247: "Pupitar", 248: "Tyranitar", 249: "Lugia", 250: "Ho-oh", 251: "Celebi",
277: "Treecko", 278: "Grovyle", 279: "Sceptile", 280: "Torchic", 281: "Combusken", 282: "Blaziken", 283: "Mudkip", 284: "Marshtomp", 285: "Swampert", 286: "Poochyena", 287: "Mightyena", 288: "Zigzagoon", 289: "Linoone", 290: "Wurmple", 291: "Silcoon", 292: "Beautifly", 293: "Cascoon", 294: "Dustox", 295: "Lotad", 296: "Lombre", 297: "Ludicolo", 298: "Seedot", 299: "Nuzleaf", 300: "Shiftry", 301: "Nincada", 302: "Ninjask", 303: "Shedinja", 304: "Taillow", 305: "Swellow", 306: "Shroomish", 307: "Breloom", 308: "Spinda", 309: "Wingull", 310: "Pelipper", 311: "Surskit", 312: "Masquerain", 313: "Wailmer", 314: "Wailord", 315: "Skitty", 316: "Delcatty", 317: "Kecleon", 318: "Baltoy", 319: "Claydol", 320: "Nosepass", 321: "Torkoal", 322: "Sableye", 323: "Barboach", 324: "Whiscash", 325: "Luvdisc", 326: "Corphish", 327: "Crawdaunt", 328: "Feebas", 329: "Milotic", 330: "Carvanha", 331: "Sharpedo", 332: "Trapinch", 333: "Vibrava", 334: "Flygon", 335: "Makuhita", 336: "Hariyama", 337: "Electrike", 338: "Manectric", 339: "Numel", 340: "Camerupt", 341: "Spheal", 342: "Sealeo", 343: "Walrein", 344: "Cacnea", 345: "Cacturne", 346: "Snorunt", 347: "Glalie", 348: "Lunatone", 349: "Solrock", 350: "Azurill", 351: "Spoink", 352: "Grumpig", 353: "Plusle", 354: "Minun", 355: "Mawile", 356: "Meditite", 357: "Medicham", 358: "Swablu", 359: "Altaria", 360: "Wynaut", 361: "Duskull", 362: "Dusclops", 363: "Roselia", 364: "Slakoth", 365: "Vigoroth", 366: "Slaking", 367: "Gulpin", 368: "Swalot", 369: "Tropius", 370: "Whismur", 371: "Loudred", 372: "Exploud", 373: "Clamperl", 374: "Huntail", 375: "Gorebyss", 376: "Absol", 377: "Shuppet", 378: "Banette", 379: "Seviper", 380: "Zangoose", 381: "Relicanth", 382: "Aron", 383: "Lairon", 384: "Aggron", 385: "Castform", 386: "Volbeat", 387: "Illumise", 388: "Lileep", 389: "Cradily", 390: "Anorith", 391: "Armaldo", 392: "Ralts", 393: "Kirlia", 394: "Gardevoir", 395: "Bagon", 396: "Shelgon", 397: "Salamence", 398: "Beldum", 399: "Metang", 400: "Metagross", 401: "Regirock", 402: "Regice", 403: "Registeel", 404: "Kyogre", 405: "Groudon", 406: "Rayquaza", 407: "Latias", 408: "Latios", 409: "Jirachi", 410: "Deoxys", 411: "Chimecho", }

mapNat = {
277: 252, 278: 253, 279: 254, 280: 255, 281: 256, 282: 257, 283: 258, 284: 259, 285: 260, 286: 261, 287: 262, 288: 263, 289: 264, 290: 265, 291: 266, 292: 267, 293: 268, 294: 269, 295: 270, 296: 271, 297: 272, 298: 273, 299: 274, 300: 275, 301: 290, 302: 291, 303: 292, 304: 276, 305: 277, 306: 285, 307: 286, 308: 327, 309: 278, 310: 279, 311: 283, 312: 284, 313: 320, 314: 321, 315: 300, 316: 301, 317: 352, 318: 343, 319: 344, 320: 299, 321: 324, 322: 302, 323: 339, 324: 340, 325: 370, 326: 341, 327: 342, 328: 349, 329: 350, 330: 318, 331: 319, 332: 328, 333: 329, 334: 330, 335: 296, 336: 297, 337: 309, 338: 310, 339: 322, 340: 323, 341: 363, 342: 364, 343: 365, 344: 331, 345: 332, 346: 361, 347: 362, 348: 337, 349: 338, 350: 298, 351: 325, 352: 326, 353: 311, 354: 312, 355: 303, 356: 307, 357: 308, 358: 333, 359: 334, 360: 360, 361: 355, 362: 356, 363: 315, 364: 287, 365: 288, 366: 289, 367: 316, 368: 317, 369: 357, 370: 293, 371: 294, 372: 295, 373: 366, 374: 367, 375: 368, 376: 359, 377: 353, 378: 354, 379: 336, 380: 335, 381: 369, 382: 304, 383: 305, 384: 306, 385: 351, 386: 313, 387: 314, 388: 345, 389: 346, 390: 347, 391: 348, 392: 280, 393: 281, 394: 282, 395: 371, 396: 372, 397: 373, 398: 374, 399: 375, 400: 376, 401: 377, 402: 378, 403: 379, 404: 382, 405: 383, 406: 384, 407: 380, 408: 381, 409: 385, 410: 386, 411: 358,
}

mapNamesVersions = {
    'emerald': {
        0: {
            0: "Petalburg City",
            1: "Slateport City",
            5: "Lilycove City",
            6: "Mossdeep City",
            7: "Sootopolis City",
            8: "Ever Grande City",
            11: "Dewford Town",
            15: "Pacifidlog Town",
            16: "Route 101",
            17: "Route 102",
            18: "Route 103",
            19: "Route 104",
            20: "Route 105",
            21: "Route 106",
            22: "Route 107",
            23: "Route 108",
            24: "Route 109",
            25: "Route 110",
            26: "Route 111",
            27: "Route 112",
            28: "Route 113",
            29: "Route 114",
            30: "Route 115",
            31: "Route 116",
            32: "Route 117",
            33: "Route 118",
            34: "Route 119",
            35: "Route 120",
            36: "Route 121",
            37: "Route 122",
            38: "Route 123",
            39: "Route 124",
            40: "Route 125",
            41: "Route 126",
            42: "Route 127",
            43: "Route 128",
            44: "Route 129",
            45: "Route 130",
            46: "Route 131",
            47: "Route 132",
            48: "Route 133",
            49: "Route 134",
            50: "Route 124/underwater",
            51: "Route 126/underwater"},
        24: {
            0: "Meteor Falls",
            1: "Meteor Falls/back",
            2: "Meteor Falls/B1F",
            3: "Meteor Falls/back/small room",
            4: "Rusturf Tunnel",
            7: "Granite Cave/1F",
            8: "Granite Cave/B1F",
            9: "Granite Cave/B2F",
            10: "Granite Cave/1F/small Room",
            11: "Petalburg Woods",
            13: "Jagged Pass",
            14: "Fiery Pass",
            15: "Mt. Pyre/1F",
            16: "Mt. Pyre/2F",
            17: "Mt. Pyre/3F",
            18: "Mt. Pyre/4F",
            19: "Mt. Pyre/5F",
            20: "Mt. Pyre/6F",
            21: "Mt. Pyre/outside",
            22: "Mt. Pyre/summit",

            27: "Seafloor Cavern",
            28: "Seafloor Cavern",
            29: "Seafloor Cavern",
            30: "Seafloor Cavern",
            31: "Seafloor Cavern",
            32: "Seafloor Cavern",
            33: "Seafloor Cavern",
            34: "Seafloor Cavern",
            35: "Seafloor Cavern",

            37: "Cave of Origin/entrance",
            38: "Cave of Origin/1F",
            39: "Cave of Origin/B1F",
            40: "Cave of Origin/B2F",
            41: "Cave of Origin/B3F",
            43: "Victory Road/1F",
            44: "Victory Road/B1F",
            45: "Victory Road/B2F",
            46: "Shoal Cave",
            47: "Shoal Cave",
            48: "Shoal Cave",
            49: "Shoal Cave",
            52: "New Mauville/Entrance",
            53: "New Mauville",
            58: "Abondoned Ship",
            65: "Abondoned Ship",
            79: "Sky Pillar/1F",
            81: "Sky Pillar/3F",
            83: "Shoal Cave/B1F",
            84: "Sky Pillar/5F",
            86: "Magma Hideout",
            87: "Magma Hideout",
            88: "Magma Hideout",
            89: "Magma Hideout",
            90: "Magma Hideout",
            91: "Magma Hideout",
            92: "Magma Hideout",
            93: "Magma Hideout",
            94: "Mirage Tower",
            95: "Mirage Tower",
            96: "Mirage Tower",
            97: "Mirage Tower",
            98: "Desert Underpass",
            99: "Artisan Cave",
            100: "Artisan Cave",
            106: "Altering Cave", 
            107: "Meteor Falls"},
        26: {
            0: "Safari Zone/NW/mach bike area",
            1: "Safari Zone/NE/acro bike area",
            2: "Safari Zone/SW",
            3: "Safari Zone/SE",
            12: "Safari Zone/expansion north",
            13: "Safari Zone/expansion south"}},
    'firered': {
        1: {
            0: "Viridian Forest",
            1: "Mount Moon/1F",
            2: "Mount Moon/B1F",
            3: "Mount Moon/B2F",
            4: "S.S. Anne",
            37: "DIGLETT's Cave",
            39: "Victory Road/1F",
            40: "Victory Road/2F",
            41: "Victory Road/3F",
            59: u"Pok\xe9mon Mansion",
            60: u"Pok\xe9mon Mansion",
            61: u"Pok\xe9mon Mansion",
            62: u"Pok\xe9mon Mansion/B1F",
            63: "Safari Zone/center",
            64: "Safari Zone/right, area 1",
            65: "Safari Zone/top, area 2",
            66: "Safari Zone/left, area 3",
            72: "Cerulean Cave/1F",
            73: "Cerulean Cave/2F",
            74: "Cerulean Cave/B1F",
            81: "Rock Tunnel/1F",
            82: "Rock Tunnel/B1F",
            83: "Seafoam Islands/1F",
            84: "Seafoam Islands/B1F",
            85: "Seafoam Islands/B2F",
            86: "Seafoam Islands/B3F",
            87: "Seafoam Islands/B4F",
            90: u"Pok\xe9mon Tower/3F",
            91: u"Pok\xe9mon Tower/4F",
            92: u"Pok\xe9mon Tower/5F",
            93: u"Pok\xe9mon Tower/6F",
            94: u"Pok\xe9mon Tower/7F",
            95: "Power Plant",
            97: "Mt. Ember",
            98: "Mt. Ember/cave",
            99: "Mt. Ember/inside",
            100: "Mt. Ember/cave",
            103: "Mt. Ember/1F, cave behind team rocket",
            104: "Mt. Ember/B1F",
            105: "Mt. Ember/B2F",
            106: "Mt. Ember/B3F",
            107: "Mt. Ember/B2F",
            108: "Mt. Ember/B1F",
            109: "Berry Forest",
            110: "Icefall Cave/entrance",
            111: "Icefall Cave/1F",
            112: "Icefall Cave/B1F",
            113: "Icefall Cave/waterfall",
            121: "Patern Bush",
            122: "Altering Cave"},
        2: {  
            13: "Lost Cave/room 1",
            14: "Lost Cave/room 2",
            15: "Lost Cave/room 3",
            16: "Lost Cave/room 4",
            17: "Lost Cave/room 5",
            18: "Lost Cave/room 6",
            19: "Lost Cave/room 7",
            20: "Lost Cave/room 8",
            21: "Lost Cave/room 9",
            22: "Lost Cave/room 10",
            23: "Lost Cave/item rooms",
            24: "Lost Cave/item rooms",
            25: "Lost Cave/item rooms",
            26: "Lost Cave/item rooms",
            27: "Monean Chamber",
            28: "Liptoo Chamber",
            29: "Weepth Chamber",
            30: "Dilford Chamber",
            31: "Scufib Chamber",
            32: "Rixy Chamber",
            33: "Viapos Chamber"},
        3: {
            0: "Pallet Town",
            1: "Viridian City",
            3: "Cerulean City",
            5: "Vermillion City",
            6: "Celadon City",
            7: "Fuchsia City",
            8: "Cinnabar Island",
            12: "One Island",
            15: "Four Island",
            16: "Five Island",
            19: "Route 1",
            20: "Route 2",
            21: "Route 3",
            22: "Route 4",
            23: "Route 5",
            24: "Route 6",
            25: "Route 7",
            26: "Route 8",
            27: "Route 9",
            28: "Route 10",
            29: "Route 11",
            30: "Route 12",
            31: "Route 13",
            32: "Route 14",
            33: "Route 15",
            34: "Route 16",
            35: "Route 17",
            36: "Route 18",
            37: "Route 19",
            38: "Route 20",
            39: "Route 21",
            40: "Route 21",
            41: "Route 22",
            42: "Route 23",
            43: "Route 24",
            44: "Route 25",
            45: "Kindle Road",
            46: "Treasure Beach",
            47: "Cape Brink",
            48: "Bond Bridge",
            49: "Three Isle Port",
            54: "Resort Gorgeous",
            55: "Water Labyrinth",
            56: "Five Isle Meadow",
            57: "Memorial Pillar",
            58: "Outcast Island",
            59: "Green Path",
            60: "Water Path",
            61: "Ruin Valley",
            62: "Trainer Tower",
            63: "Canyon Entrance",
            64: "Sevault Canyon",
            65: "Tanoby Ruins"}},
}

mapNamesVersions['sapphire'] = mapNamesVersions['emerald']
mapNamesVersions['ruby'] = mapNamesVersions['emerald']
mapNamesVersions['leafgreen'] = mapNamesVersions['firered']



#########

main2()
