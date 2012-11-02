import genshi.template, sys, os, subprocess
from signatures import getDumpInfo
import query
from config import getconfig
from classifier import classifierFilters

config = getconfig()

thisdir = os.path.dirname(__file__)
tmpl = genshi.template.MarkupTemplate(open(os.path.join(thisdir, 'nightly.xhtml')))

def makeNightlyReport(date):
    reports = query.filterReportsForDateRange(date, date, classifierFilters)

    reports.sort(key=lambda d: d[0].json['submitted_timestamp'])

    classifications = {}
    for report, metadict in reports:
        key = metadict.get('classifiedas', None)
        classifications[key] = classifications.get(key, 0) + 1

    s = tmpl.generate(date=date, reports=reports, classifications=classifications)

    dailydir = os.path.join(config.minidump_storage_path, str(date.year),
                            date.strftime('%m-%d'))
    reportfile = os.path.join(dailydir, 'nightly.html')
    fd = open(reportfile, 'w')
    fd.write(s.render('html'))
    fd.close()

    if config.reporting_server and config.reporting_directory:
        remoteDir = os.path.join(config.reporting_directory, str(date.year),
                                 date.strftime('%m-%d'))
        remoteFile = os.path.join(remoteDir, 'nightly.html')

        fd = open(reportfile)
        subprocess.check_call(['ssh', config.reporting_server,
                               'mkdir', '-p', remoteDir, '&&', 'cat', '>',
                               remoteFile], stdin=fd)
        fd.close()

if __name__ == '__main__':
    from datetime import datetime, timedelta
    from optparse import OptionParser

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
        makeNightlyReport(date)
        date += timedelta(days=1)
