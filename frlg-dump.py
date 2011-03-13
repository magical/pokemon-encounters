from sys import stdout

from gba.frlg_dump import to_xml, versions
from lxml.etree import Element, ElementTree

root = Element('wild')
for version in  versions:
    f = open("data/wild-{}.bin".format(version), 'rb')
    game = to_xml(f, version)
    root.append(game)

tree = ElementTree(root)

stdout.write('''<?xml version="1.0" encoding="utf-8"?>''')
tree.write(stdout, pretty_print=True)
