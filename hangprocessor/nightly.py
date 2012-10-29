import genshi.template, sys, os, subprocess
import datetime
from signatures import getDumpInfo
import query
from config import getconfig

config = getconfig()

thisdir = os.path.dirname(__file__)
tmpl = genshi.template.MarkupTemplate(open(os.path.join(thisdir, 'nightly.xhtml')))

def makeNightlyReport(date):
    reports = query.getReportsForDate(date)

    reports.sort(key=lambda d: d.json['submitted_timestamp'])

    s = tmpl.generate(date=date, reports=reports)

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
    date, = sys.argv[1:]
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    makeNightlyReport(date)