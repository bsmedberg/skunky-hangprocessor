import sys
from hangprocessor.query import filterReportsForDateRange
from optparse import OptionParser
from datetime import datetime, timedelta

searchSignatures = [
    "F_1152915508___________________________________",
    "mozilla::plugins::PluginInstanceChild::UpdateWindowAttributes(bool)",
    "mozilla::ipc::RPCChannel::Call(IPC::Message*, IPC::Message*)"
]

def findFirstFrame(thread, start, signature):
    for idx in xrange(start, len(thread.frames)):
        frame = thread.frames[idx]
        if frame.normalized == signature:
            return idx + 1

    return None

def filterSearch(i):
    """
    Find only reports in which the plugin stack contains the search signatures
    in order, and annotate the frame above the last (RPCChannel::Call)
    signature.
    """

    report, metadict = i

    if 'plugin' not in report.dumps:
        return False

    pdump = report.dumps['plugin']
    if pdump.error or not pdump.crashthread in pdump.threads:
        return False

    thread = pdump.threads[pdump.crashthread]

    start = 0

    for signature in searchSignatures:
        start = findFirstFrame(thread, start, signature)
        if start is None:
            return False

    metadict['callsig'] = thread.frames[start].normalized
    return True

yesterday = datetime.now() - timedelta(days=1)
    
o = OptionParser("usage: %prog [options]")
o.add_option('--start-date', '-s', dest='startdate', metavar="YYYY-MM-DD", default=yesterday.strftime('%Y-%m-%d'))
o.add_option('--end-date', '-e', dest='enddate', metavar="YYYY-MM-DD", default=yesterday.strftime('%Y-%m-%d'))

opts, args = o.parse_args()

if len(args):
    o.print_help()
    sys.exit(1)

startdate = datetime.strptime(opts.startdate, '%Y-%m-%d')
enddate = datetime.strptime(opts.enddate, '%Y-%m-%d')

reports = filterReportsForDateRange(startdate, enddate, [filterSearch])

print "Reports from %s to %s" % (startdate.strftime('%Y-%m-%d'),
                                 enddate.strftime('%Y-%m-%d'))
print "plugin-container stack matches pattern:"
for sig in searchSignatures:
    print "\t%s" % sig

print "Reporting: p-c signature, IPC call immediately above %s" % (searchSignatures[-1])
print

for report, metadict in reports:
    print '%s:' % report.id
    print '\t%s' % report.dumps['plugin'].signature
    print '\t%s' % metadict['callsig']
