#!/usr/bin/env python3

from struct import pack, unpack

# /a/0/1/2
f = open("bw-table.narc", "rb")
f.seek(0x3c)


location_names_kana = list(map(str.strip,
    open("bw-location-names-kana", "r", encoding="utf-8")))
location_names_kanji = list(map(str.strip,
    open("bw-location-names-kanji", "r", encoding="utf-8")))
location_names_en = list(map(str.strip,
    open("bw-locations-en", "r", encoding="utf-8")))

class namespace(object):
    pass


def read_encounters():
    while 1:
        data = f.read(0x30)
        if not data:
            break

        ns = namespace()

        ns.encounter_id, = unpack("<h", data[0x14:0x16])
        if ns.encounter_id == -1:
            continue

        ns.location_name_id, = unpack("B", data[0x1a:0x1b])

        ns.kana = location_names_kana[ns.location_name_id]
        ns.kanji = location_names_kanji[ns.location_name_id]
        ns.en = location_names_en[ns.location_name_id]

        yield ns


print("id,location_internal_id,location,area")
for x in read_encounters():
    print("{x.encounter_id},{x.location_name_id},{x.en},".format(x=x))
