from sys import stdout


f = open("data/wild-black.narc", 'rb')

#from nds.bw_dump import dump_text
#dump_text(f, stdout)

from nds.bw_dump import dump_xml
dump_xml(f, stdout)
