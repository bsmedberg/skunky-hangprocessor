import query

def filterOnMetadata(i):
    report, metadict = i

    if 'plugin' not in report.dumps:
        return False

    if report.dumps['plugin'].os != 'Windows NT':
        return False

    if report.json.get('ProductName', None) != 'Firefox':
        return False

    version = report.json.get('Version', None)
    if version is None:
        return False

    metadict['version'] = version

    channel = report.json.get('ReleaseChannel', None)
    if channel not in ('nightly', 'aurora'):
        return False

    metadict['channel'] = channel

    duration = report.json.get('PluginHangUIDuration', None)
    if duration != None:
        duration = int(duration)
        duration = duration - (duration % 5000) # bucket by 5 seconds

    metadict['duration'] = duration

    return True

def summaryForDate(date):
    summarymap = {} # (channel, duration) -> count
    reports = query.filterReportsForDateRange(date, date, [filterOnMetadata])
    
    for report, metadict in reports:
        key = (metadict['channel'], metadict['duration'])
        if key in summarymap:
            summarymap[key] += 1
        else:
            summarymap[key] = 1

    return summarymap

if __name__ == '__main__':
    import os, csv, sys
    from datetime import datetime, timedelta
    from optparse import OptionParser
    from config import getconfig

    yesterday = datetime.utcnow() - timedelta(days=1)
    
    o = OptionParser("usage: %prog [options]")
    o.add_option('--start-date', '-s', dest='startdate', metavar="YYYY-MM-DD", default=yesterday.strftime('%Y-%m-%d'))
    o.add_option('--end-date', '-e', dest='enddate', metavar="YYYY-MM-DD", default=yesterday.strftime('%Y-%m-%d'))

    opts, args = o.parse_args()

    if len(args):
        o.print_help()
        sys.exit(1)

    startdate = datetime.strptime(opts.startdate, '%Y-%m-%d')
    enddate = datetime.strptime(opts.enddate, '%Y-%m-%d')

    date = startdate
    while date <= enddate:
        s = summaryForDate(date)

        resfile = os.path.join(getconfig().minidump_storage_path, str(date.year),
                               date.strftime('%m-%d'), 'daily-summary.csv')

        fd = open(resfile, 'w')
        w = csv.writer(fd, dialect='excel-tab')
        for (channel, duration), count in s.iteritems():
            w.writerow((channel, duration, count))
        fd.close()

        date += timedelta(days=1)
