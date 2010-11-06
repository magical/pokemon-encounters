from sys import stdout

from nds.bw_dump import dump_text

f = open("data/wild-black.narc", 'rb')

dump_text(f, stdout)
