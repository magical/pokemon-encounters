#!/usr/bin/env python3

from struct import pack, unpack

# /a/0/1/2
f = open("bw2-table.narc", "rb")
f.seek(0x3c)


location_names_en = list(map(str.strip,
    open("bw2-location-names-en", "r", encoding="utf-8")))

class namespace(object):
    pass

def read_encounters():
    while 1:
        data = f.read(0x30)
        if not data:
            break

        ns = namespace()

        ns.encounter_id, = unpack("<H", data[0x14:0x16])
        ns.encounter_id &= 0xfff
        if ns.encounter_id == 0xfff:
            continue

        ns.location_name_id, = unpack("B", data[0x1a:0x1b])

        ns.en = location_names_en[ns.location_name_id]

        yield ns

print("id,location_internal_id,location,area")
encounters = list(read_encounters())
for x in sorted(encounters, key=lambda x: (x.location_name_id, x.encounter_id)):
    if 1 == sum(1 for y in encounters if x.location_name_id == y.location_name_id):
        area = ""
    else:
        area = "unknown area {}".format(x.encounter_id)
    print("{x.encounter_id},{x.location_name_id},{x.en},{area}".format(x=x, area=area))
