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

Dump = namedtuple('Dump', ('os', 'signature'))

def getDumpInfo(fd):
    signatureList = []
    crashthread = None
    dumpos = None
    for line in fd:
        line = line.strip()
        items = map(emptyFilter, line.split('|'))

        key = items.pop(0)
        if key is None:
            continue

        if key == 'OS':
            dumpos, osversion = items
            if dumpos == 'Windows NT':
                makelowercase = True
            else:
                makelowercase = False
        elif key == 'Crash':
            reason, address, crashthread = items
        elif key == crashthread:
            frame_num, module_name, function, source, source_line, instruction = items
            if int(frame_num) > 30:
                continue
            if makelowercase and module_name is not None:
                module_name = module_name.lower()
            signatureList.append(c_tool.normalize_signature(module_name, function, source, source_line, instruction))

    return Dump(dumpos, c_tool.generate(signatureList, -1, crashthread)[0])

if __name__ == '__main__':
    import sys
    for f in sys.argv[1:]:
        fd = open(f)
        print "%s: %r" % (f, getDumpInfo(fd))
        fd.close()
