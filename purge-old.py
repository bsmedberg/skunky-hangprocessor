import os, sys, datetime, re, shutil
from optparse import OptionParser
from hangprocessor.config import getconfig

datadir = getconfig().minidump_storage_path

def parsedays(option, opt, value, parser):
    setattr(parser.values, option.dest, datetime.datetime.utcnow() - datetime.timedelta(days=value))

o = OptionParser()
o.add_option('--days', action="callback", dest="startdate", type="int", nargs=1, callback=parsedays, default=(datetime.datetime.utcnow() - datetime.timedelta(days=61)))

opts, args = o.parse_args()
if len(args):
    o.print_help()
    sys.exit(1)

yearre = re.compile(r'\d{4}$')
dayre = re.compile(r'(\d{2})-(\d{2})$')

for year in os.listdir(datadir):
    if yearre.match(year) is None:
        continue

    intyear = int(year)

    for entry in os.listdir(os.path.join(datadir, year)):
        dir = os.path.join(datadir, year, entry)

        m = dayre.match(entry)
        if m is None:
            continue

        month, day = map(int, m.group(1, 2))

        date = datetime.datetime(intyear, month, day)
        if date < opts.startdate:
            shutil.rmtree(dir)
