
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

import csv
with open("rby-locations.csv", 'wb') as f:
    writer = csv.writer(f)
    writer.writerow('id location area'.split())
    for id, name in sorted(mapNamesVersions['red'].items()):
        location, _, area = name.partition('/')
        writer.writerow((id, location.encode('utf-8'), area.encode('utf-8')))
