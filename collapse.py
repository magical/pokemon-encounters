import sys
from warnings import warn
from lxml.etree import Element, parse as parse_xml
from itertools import groupby
from functools import reduce
from copy import deepcopy
import operator
from collections import OrderedDict as odict

class NotEqual(ValueError):
    pass

def get_methods(eArea):
    """Return the set of methods which are defined in the given area."""
    methods = set()
    for monsters in eArea.findall('monsters'):
        methods.add(monsters.get('method'))
    return methods

#def merge_areas(a, b):
#    """Merge the <monsters>s in two areas to make a new area.
#
#    Elements may be reused from one of the old areas, so the old areas should
#    not be used after calling this function.
#
#    Both areas must have the same structure. By which i mean that the layout
#    of the <monsters>s must be the same in each <area>, otherwise the recursive
#    merge will get confused. If you have two areas which do not have the same
#    structure, you must normalize them somehow first.
#
#    Only whole methods can go missing. Missing conditions will be treated as
#    an error.
#
#    This function may raise NotEqual if the areas are too dissimilar.
#
#    """
#    methods_a = get_methods(a)
#    methods_b = get_methods(b)
#
#    missing = methods_a ^ methods_b
#
#    eNewArea = Element('area')
#    eNewArea.attrib.update(a.attrib)
#
#    def pokemons_equal(eA, eB):
#        for e1, e2 in zip(eA, eB):
#            assert 'pokemon' == e1.tag == e2.tag
#            if not all(e1.get(attr) == e2.get(attr)
#                       for attr in ('number', 'level', 'form')):
#                return False
#        return True
#
#    def merge_monsters(eA, eB):
#        for e in a:
#            assert e.tag == 'monsters'
#
#            if e.get('method') in missing:
#                pass
#            else:
#                eOther = find_monsters(b, e)
#                merge_monsters(e, eOther)
#
#        for method in sorted(methods):
#            for eArea, area_methods in zip(areas, areas_methods):
#                if method in area_methods:
#                    # copy over all <monsters> of said method
#                    for monsters in area:
#                        if monsters.get('method') == method:
#                            eNewArea.append(deepcopy(monsters))
#                    break
#            else:
#                raise RuntimeError('method {:r} not found?'.format(method))
#
#        return eNewArea
#
#
#    if all(e.tag == 'monsters' for e in eAreaA):
#        assert all(e.tag == 'monsters' for e in eAreaB):
#
#        return merge_monsters(eAreaA, eAreaB)
#
#    elif all(e.tag == 'pokemon' for e in eAreaA):
#        assert all(e.tag == 'pokemon' for e in eAreaB):
#
#        if pokemons_equal(eAreaA, eAreaB):
#            return eAreaA
#        else:
#            raise NotEqual
#
#    else:
#        raise ValueError("subelements of <area> must all be <pokemon> or all be <monsters>")


def pokemon_equal(eA, eB):
    return all(eA.get(attr) == eB.get(attr)
               for attr in ('number', 'levels', 'form'))

def monster_attribs_equal(eA, eB):
    return eA.items() == eB.items()

def merge_areas(a, b):
    """Merge the <monsters>s in two areas to make a new area.

    Elements may be reused from one of the old areas, so the old areas should
    not be used after calling this function.

    Both areas must have the same structure. By which i mean that the layout
    of the <monsters>s must be the same in each <area>, otherwise the recursive
    merge will get confused. If you have two areas which do not have the same
    structure, you must normalize them somehow first.

    Only whole methods can go missing. Missing conditions will be treated as
    an error.

    This function may raise NotEqual if the areas are too dissimilar.

    """
    methods_a = get_methods(a)
    methods_b = get_methods(b)

    common = methods_a & methods_b

    iter_a = iter(a)
    iter_b = iter(b)
    eA, eB = next(iter_a), next(iter_b)
    try:
        while True:
            while eA.tag == 'monsters' and eA.get('method') not in common:
                eA = next(iter_a)

            while eB.tag == 'monsters' and eB.get('method') not in common:
                a.insert(a.index(eA), eB)
                eB = next(iter_b)

            if eA.tag == 'monsters' and eB.tag == 'monsters':
                if not monster_attribs_equal(eA, eB):
                    raise NotEqual
                else:
                    eNew = merge_areas(eA, eB)
                    a.replace(eA, eNew)
            elif eA.tag == 'pokemon' and eB.tag == 'pokemon':
                if not pokemon_equal(eA, eB):
                    raise NotEqual
            else:
                raise ValueError(eA, eB)
            eA, eB = next(iter_a), next(iter_b)
    except StopIteration:
        pass

    for e in iter_a:
        if e.tag == 'monsters':
            pass
        else:
            raise NotEqual

    for e in iter_b:
        if e.tag == 'monsters':
            a.append(e)

    return a


def collapse(xml):
    for eLocation in xml.xpath("/wild/game/location"):
        areas = eLocation.xpath("area")

        grouped_areas = odict()
        for area in areas:
            grouped_areas.setdefault(area.get('name'), []).append(area)

        for area_name, group in grouped_areas.items():
            group = list(group)
            if len(group) > 1:
                # If the areas have the same name and are identical, collapse
                # them. If they are not identical, give a warning
                #
                # This is made slightly trickier because otherwise-identical
                # areas may omit encounters for some methods; for example, 
                # one area may define Rock Smash encounters, or one area may
                # not contain water and thus does not define surfing or fishing
                # encounters.

                index = eLocation.index(group[0])
                try:
                    eNewArea = reduce(merge_areas, group)
                except NotEqual:
                    warn('Areas named "{}/{}" are not identical and cannot be collapsed'.format(eLocation.get('name'), area_name))
                else:
                    for eArea in group:
                        eLocation.remove(eArea)
                    eLocation.insert(index, eNewArea)
            else:
                #print("Ignoring {}/{}".format(eLocation.get('name'), area_name), file=sys.stderr)
                pass

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    try:
        filename = args[0]
    except IndexError:
        filename = '-'

    xml = parse_xml(
        filename if filename != '-' else sys.stdin
    )
    collapse(xml)
    xml.write(sys.stdout.buffer, pretty_print=True)

if __name__ == "__main__":
    sys.exit(main())
