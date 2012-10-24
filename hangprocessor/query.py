import os, json
from signatures import getDumpInfo
from config import getconfig
from collections import namedtuple
import datetime
import itertools

config = getconfig()
Report = namedtuple('Report', ('id', 'json', 'dumps'))

def getReportsForDate(date):
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

    return reports

def getReportsForDateRange(startdate, enddate, filters):
    reports = []
    
    date = startdate
    while startdate <= enddate:
        datereports = getReportsForDate(date)
        
        for filter in filters:
            datereports = itertools.ifilter(filter, datereports)

        reports.extend(datereports)

    return reports
