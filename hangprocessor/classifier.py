"""The primary export of this file is `classifierFilters`, a list of filter
functions for query.py. These functions will perform the following tasks:

* Filter out Nightly and Aurora builds before bug 788512 landed. Add metadict['error'] for reports
  which are incomplete or have processing errors.
* Classify the remaining hangs by adding metadict entries 'classifiedas' and
  'classifydata', both strings
* The classifiers may also add additional classifier-specific metadict entries.
"""

import datetime

first19 = datetime.date(2012, 10, 17)
first18 = datetime.date(2012, 10, 23)

def filterUnwantedReports(i):
    report, metadict = i

    metadict['error'] = False

    if report.json.get('ProductName', None) != 'Firefox':
        return False

    version = report.json.get('Version', None)
    if version is None:
        return False

    try:
        majorversion = int(version.split('.')[0])
    except ValueError:
        return False

    buildid = report.json.get('BuildID', None)
    if buildid is None:
        return False

    try:
        builddate = datetime.date(int(buildid[0:4]), int(buildid[4:6]), int(buildid[6:8]))
    except ValueError:
        return False

    if majorversion < 17:
        return False
    elif majorversion == 18:
        if builddate < first18:
            return False
    elif builddate < first19:
        return False

    if 'plugin' not in report.dumps:
        return False

    if report.dumps['plugin'].cpu == 'amd64':
        return False

    for dump in report.dumps.itervalues():
        if dump.error or not dump.crashthread in dump.threads:
            metadict['error'] = True
            metadict['classifiedas'] = 'processing-error'
            break

    return True

def findFirstFrame(thread, start, signature):
    for idx in xrange(start, len(thread.frames)):
        frame = thread.frames[idx]
        if frame.normalized == signature:
            return idx + 1

    return None

updateWindowAttributesSignatures = [
    "F_1152915508___________________________________",
    "mozilla::plugins::PluginInstanceChild::UpdateWindowAttributes(bool)",
    "mozilla::ipc::RPCChannel::Call(IPC::Message*, IPC::Message*)"
]

def classifyUpdateWindowAttributes(i):
    """
    Find only reports in which the plugin stack contains the search signatures
    in order, and annotate the frame above the last (RPCChannel::Call)
    signature.
    """

    report, metadict = i

    if metadict['error']:
        return True

    pdump = report.dumps['plugin']

    thread = pdump.threads[pdump.crashthread]

    start = 0

    for signature in updateWindowAttributesSignatures:
        start = findFirstFrame(thread, start, signature)
        if start is None:
            return True
        
    metadict['classifiedas'] = 'adbe-3355131'
    metadict['classifydata'] = thread.frames[start].normalized

    return True

def topOfStackContains(stack, signature, frameCount=5):
    for i in xrange(0, min(len(stack.frames), frameCount)):
        if stack.frames[i].normalized.startswith(signature):
            return True

    return False

def classifySetWindowPos(i):
    report, metadict = i

    if metadict['error'] or 'classifiedas' in metadict:
        return True

    pdump = report.dumps['plugin']
    crashthread = pdump.threads[pdump.crashthread]
    if topOfStackContains(crashthread, 'NtUserSetWindowPos'):
        if topOfStackContains(crashthread, 'F_320940052'):
            c = 'NtUserSetWindowPos | F_320940052'
        elif topOfStackContains(crashthread, 'F_1378698112'):
            c = 'NtUserSetWindowPos | F_1378698112'
        elif topOfStackContains(crashthread, 'F_468782153'):
            c = 'NtUserSetWindowPos | F_468782153'
        else:
            c = 'NtUserSetWindowPos | other'

        metadict['classifiedas'] = c
        return True

    if not 'flash2' in report.dumps:
        return True

    dump = report.dumps['flash2']
    crashthread = dump.threads[dump.crashthread]
    if topOfStackContains(crashthread, 'NtUserSetWindowPos'):
        if topOfStackContains(crashthread, 'F455544145'):
            c = 'NtUserSetWindowPos | F455544145'
        else:
            c = 'NtUserSetWindowPos | other'
        metadict['classifiedas'] = c

    return True

def classifySendWaitReceivePort(i):
    report, metadict = i

    if metadict['error'] or 'classifiedas' in metadict:
        return True

    if not 'flash2' in report.dumps:
        return True

    dump = report.dumps['flash2']
    crashthread = dump.threads[dump.crashthread]
    if topOfStackContains(crashthread, 'NtAlpcSendWaitReceivePort'):
        metadict['classifiedas'] = 'NtAlpcSendWaitReceivePort'

    return True

def classifyBug811804(i):
    report, metadict = i
    if metadict['error'] or 'classifiedas' in metadict:
        return True

    if not 'flash2' in report.dumps:
        return True

    dump = report.dumps['flash2']
    if dump.signature == 'hang | NtUserWaitMessage | F340331645________________________________':
        metadict['classifiedas'] = 'bug811804-NtUserWaitMessage'

    return True

def classifyBug812318(i):
    report, metadict = i
    if metadict['error'] or 'classifiedas' in metadict:
        return True

    if not 'flash2' in report.dumps:
        return True

    dump = report.dumps['flash2']
    crashthread = dump.threads[dump.crashthread]
    if topOfStackContains(crashthread, 'NtUserPeekMessage'):
        if topOfStackContains(crashthread, 'F849276792______________________________'):
            metadict['classifiedas'] = 'bug812318-PeekMessage'
        else:
            metadict['classifiedas'] = 'NtUserPeekMessage-other'

    return True

classifierFilters = [
    filterUnwantedReports,
    classifyUpdateWindowAttributes,
    classifySetWindowPos,
    classifySendWaitReceivePort,
    classifyBug811804,
    classifyBug812318,
]
