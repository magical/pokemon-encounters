from sys import stdout

from gba.rse_dump import to_xml, load_locations
from lxml.etree import Element, ElementTree

load_locations()
root = Element('wild')
for version in  ('ruby', 'sapphire', 'emerald'):
    f = open("data/wild-{}.bin".format(version), 'rb')
    xml = to_xml(f)
    game = xml.xpath('/wild/game')[0]
    game.set('version', version) #XXX
    root.append(game)

tree = ElementTree(root)

stdout.write('''<?xml version="1.0" encoding="utf-8"?>''')
tree.write(stdout, pretty_print=True)
