from socorro.processor.signature_utilities import CSignatureTool
from socorro.lib.util import DotDict, emptyFilter
import processorconfig as old
from collections import namedtuple

sigconfig = DotDict()
sigconfig.irrelevant_signature_re = old.irrelevantSignatureRegEx.default
sigconfig.prefix_signature_re = old.prefixSignatureRegEx
sigconfig.signatures_with_line_numbers_re = old.signaturesWithLineNumbersRegEx.default
sigconfig.signature_sentinels = old.signatureSentinels.default
c_tool = CSignatureTool(sigconfig)

Dump = namedtuple('Dump', ('os', 'signature', 'contents', 'error', 'threads', 'crashthread'))

class ThreadList(dict):
    def ensure(self, threadnum):
        if not threadnum in self:
            self[threadnum] = Thread(threadnum)

    def __iter__(self):
        l = self.keys()
        l.sort()
        return (self[k] for k in l)

class Thread(object):
    def __init__(self, thread_num):
        self.thread_num = thread_num
        self.frames = []

    def append(self, thread_num, frame_num, module_name, function, source, source_line, instruction):
        thread_num = int(thread_num)
        frame_num = int(frame_num)

        if thread_num != self.thread_num or frame_num != len(self.frames):
            raise Exception("Mismatch length: got %i:%i expected %s:%s" % (thread_num, frame_num, self.thread_num, len(self.frames)))

        normalized = c_tool.normalize_signature(module_name, function, source, source_line, instruction)

        self.frames.append(Frame(frame_num, module_name, function, source, source_line, instruction, normalized))

    def finish(self):
        self.signature = c_tool.generate([frame.normalized for frame in self.frames][:30], -1, self.thread_num)[0]
        
Frame = namedtuple('Frame', ('frame_num', 'module_name', 'function', 'source', 'source_line', 'instruction', 'normalized'))

def getDumpInfo(basepath):
    processedpath = basepath + '.processed'

    try:
        contents = open(processedpath).read()
    except (OSError, IOError):
        errpath = basepath + '.processingerror'
        try:
            contents = open(errpath).read()
        except (OSError, IOError):
            contents = ''
        return Dump(None, '<error>', contents, True, [], None)

    crashthread = None
    dumpos = None

    i = iter(contents.splitlines())
    for line in i:
        items = map(emptyFilter, line.split('|'))

        key = items.pop(0)
        if key is None:
            break

        if key == 'OS':
            dumpos, osversion = items
            if dumpos == 'Windows NT':
                makelowercase = True
            else:
                makelowercase = False
        elif key == 'Crash':
            reason, address, crashthread = items
            if reason == 'No crash':
                crashthread = '0'
            crashthread = int(crashthread)

    threads = ThreadList()
    for line in i:
        items = map(emptyFilter, line.split('|'))
        if len(items) != 7:
            continue

        thread_num, frame_num, module_name, function, source, source_line, instruction = items
        thread_num = int(thread_num)
        if not thread_num in threads:
            threads[thread_num] = Thread(thread_num)

        if makelowercase and module_name is not None:
            module_name = module_name.lower()
        threads[thread_num].append(thread_num, frame_num, module_name, function, source, source_line, instruction)

    for thread in threads:
        thread.finish()

    if crashthread is None:
        signature = "EMPTY: no crashing thread identified"
    elif not crashthread in threads:
        signature = "EMPTY: no data for crashing thread"
    else:
        signature = threads[crashthread].signature

    return Dump(dumpos, signature, contents, False, threads, crashthread)

if __name__ == '__main__':
    import sys
    for f in sys.argv[1:]:
        print "%s: %r" % (f, getDumpInfo(f))
