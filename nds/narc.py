# Borrowed from http://git.veekun.com/porigon-z.git

from construct import *

__all__ = ('parse_narc',)

# http://www.pipian.com/ierukana/hacking/ds_nff.html
# Nitro is used to clump binary blocks together
nitro_struct = Struct('nitro',
    Const(String('magic', 4), "NARC"),
    Const(ULInt16('bom'), 0xFFFE),
    ULInt16('unknown1'),  # always 0x0100?
    ULInt32('file_size'),
    ULInt16('unknown2'),
    ULInt16('num_records'),

    Array(
        lambda ctx: ctx['num_records'],
        Struct('records',
            String('magic', 4),
            ULInt32('length'),
            # The above fields count against the length, so subtract their size
            Field('data', lambda ctx: ctx['length'] - 8),
        ),
    ),
)

# http://www.pipian.com/ierukana/hacking/ds_narc.html
# NARC files are an extension of Nitro, used for arrays of small binary blocks
narc_fatb_struct = Struct('fatb',
    ULInt32('num_records'),
    Array(
        lambda ctx: ctx['num_records'],
        Struct('records',
            ULInt32('start'),
            ULInt32('end'),
        ),
    ),
)
narc_fntb_struct = Struct('fntb',
    ULInt32('unknown1'),
    ULInt32('unknown2'),
    # There are actually fatb.num_records of these, but that is hard to get
    # with my piecemeal parsing, so we just slurp until we run out of data
    OptionalGreedyRepeater(
        Struct('filenames',
            ULInt8('length'),
            MetaField('filename', lambda ctx: ctx['length']),
        ),
    ),
)
# There's also an FIMG block in a NARC file, but alas, we don't do all three
# blocks at once and this one needs the offsets from the FATB.  Outside code
# has to parse this.

def parse_narc(f):
    """Parse a NARC file and return a list of the contents."""
    nitro = nitro_struct.parse(f.read())

    assert nitro.records[0].magic == "BTAF"
    assert nitro.records[1].magic == "BTNF"
    assert nitro.records[2].magic == "GMIF"

    fatb = narc_fatb_struct.parse(nitro.records[0].data)
    fntb = narc_fntb_struct.parse(nitro.records[1].data)
    fimg_data = nitro.records[2].data

    fimg = []
    for fatb_record in fatb.records:
        data = fimg_data[fatb_record.start:fatb_record.end]
        fimg.append(data)

    return fimg
