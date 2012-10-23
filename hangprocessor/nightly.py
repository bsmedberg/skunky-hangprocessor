import genshi.template, sys, os, json, subprocess
from collections import namedtuple
import datetime
from signatures import getDumpInfo

thisdir = os.path.dirname(__file__)
tmpl = genshi.template.MarkupTemplate(open(os.path.join(thisdir, 'nightly.xhtml')))

Report = namedtuple('Report', ('id', 'json', 'dumps'))

def makeNightlyReport(config, date):
    dailydir = os.path.join(config.minidump_storage_path, str(date.year),
                            date.strftime('%m-%d'))

    reports = []
    for dumpid in os.listdir(dailydir):
        dumpdir = os.path.join(dailydir, dumpid)
        extrafile = os.path.join(dumpdir, 'extra.json')
        if not os.path.exists(os.path.join(dumpdir, 'extra.json')):
            continue

        extra = json.load(open(extrafile))

        dumps = {}
        def loadDump(name):
            basepath = os.path.join(dumpdir,
                                    'minidump_%s.dmp' % name)
            dumps[name] = getDumpInfo(basepath)

        loadDump('plugin')
        for d in extra.get(u'additional_minidumps', '').split(','):
            loadDump(d)

        reports.append(Report(dumpid, extra, dumps))

    reports.sort(key=lambda d: d.json['submitted_timestamp'])

    s = tmpl.generate(date=date, reports=reports)
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
    from config import getconfig

    date, = sys.argv[1:]
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    makeNightlyReport(getconfig(), date)
