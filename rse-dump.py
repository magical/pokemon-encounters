from sys import stdout


f = open("data/wild-ruby.bin", 'rb')

#from nds.bw_dump import dump_text
#dump_text(f, stdout)

from gba.rse_dump import dump_xml
dump_xml(f, stdout)
