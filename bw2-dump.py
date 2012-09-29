#!/usr/bin/env python2

from sys import stdout

from nds.bw_dump import to_xml, dump_text, VERSIONS
from lxml.etree import ElementTree, Element

root = Element('wild')
for version in ('black2', 'white2'):
    f = open("data/wild-%s.narc" % version, 'rb')
    #dump_text(f, stdout)
    root.append(to_xml(f, version))

ElementTree(root).write(stdout, encoding='utf-8', xml_declaration=True, pretty_print=True)
