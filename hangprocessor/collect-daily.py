import sys, os, csv, json, calendar
from datetime import datetime, timedelta
from optparse import OptionParser
from config import getconfig

yesterday = datetime.utcnow() - timedelta(days=1)

o = OptionParser("usage: %prog [options]")
o.add_option('--start-date', '-s', dest='startdate', metavar='YYYY-MM-DD', default='2013-01-01')
o.add_option('--end-date', '-e', dest='enddate', metavar='YYYY-MM-DD', default=yesterday.strftime('%Y-%m-%d'))

opts, args = o.parse_args()

if len(args):
    o.print_help()
    sys.exit(1)

def daterange(startdate, enddate):
    date = startdate
    while date <= enddate:
        yield date
        date += timedelta(days=1)

def getjstime(d):
    return calendar.timegm(d.timetuple()) * 1000

startdate = datetime.strptime(opts.startdate, '%Y-%m-%d').date()
enddate = datetime.strptime(opts.enddate, '%Y-%m-%d').date()

w = csv.writer(sys.stdout, dialect='excel-tab')
w.writerow(('date', 'channel', 'c'))

j = {}

for date in daterange(startdate, enddate):
    infile = os.path.join(getconfig().minidump_storage_path, str(date.year),
                          date.strftime('%m-%d'), 'daily-summary.csv')

    if not os.path.exists(infile):
        continue

    fd = open(infile)
    r = csv.reader(fd, dialect='excel-tab')

    cdata = {}

    for channel, duration, count in r:
        count = int(count)
        if not channel in cdata:
            cdata[channel] = count
        else:
            cdata[channel] += count

    fd.close()

    for channel, count in cdata.iteritems():
        if not channel in j:
            j[channel] = []

        j[channel].append([getjstime(date), count])

json.dump(j, sys.stdout)
