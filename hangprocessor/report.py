import genshi.template, sys, os, json, re

thisdir = os.path.dirname(__file__)
tmpl = genshi.template.MarkupTemplate(open(os.path.join(thisdir, 'report.xhtml')))

whitelist = set( (
    'Accessibility',
    'AdapterDeviceID',
    'AdapterVendorID',
    'additional_minidumps',
    'Add-ons',
    'BuildID',
    'CpuUsageFlashProcess1',
    'CpuUsageFlashProcess2',
    'CrashTime',
    'EMCheckCompatibility',
    'FramePoisonBase',
    'FramePoisonSize',
    'InstallTime',
    'Notes',
    'NumberOfProcessors',
    'PluginCpuUsage',
    'PluginFilename',
    'PluginHang',
    'ProcessType',
    'ProductID',
    'ProductName',
    'ReleaseChannel',
    'StartupTime',
    'submitted_timestamp',
    'Theme',
    'Throttleable',
    'Vendor',
    'Version',
    'Winsock_LSP'
) )

okchars = re.compile('[a-zA-Z0-9]+$')

def generateReport(reportdir):
    if reportdir[-1] == os.sep:
        reportdir = reportdir[:-1]

    uuid = os.path.basename(reportdir)

    extra = json.load(open(os.path.join(reportdir, 'extra.json')))

    dumps = {}

    def loaddump(name):
        basepath = os.path.join(reportdir, 'minidump_%s.dmp' % name)

        processedpath = basepath + '.processed'

        if os.path.exists(processedpath):
            dumps[name] = {'data': open(processedpath).read(),
                           'error': False}
        else:
            dumps[name] = {'data': open(basepath + '.processingerror').read(),
                           'error': True}

    loaddump('plugin')
    for d in extra[u'additional_minidumps'].split(','):
        if not okchars.match(d):
            continue

        loaddump(d)

    s = tmpl.generate(id=uuid, extra=extra, dumps=dumps, whitelist=whitelist)
    return s.render('html')

if __name__ == '__main__':
    reportdir, = sys.argv[1:]
    generateReport(reportdir)
