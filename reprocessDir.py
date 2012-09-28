import os, sys

queuedir = sys.argv[1]
dirs = sys.argv[2:]

for dir in dirs:
    dir = os.path.abspath(dir)
    for dumpdir, dirnames, filenames in os.walk(dir):
        if 'extra.json' in filenames:
            queuefile = os.path.join(queuedir, os.path.basename(dumpdir))
            if not os.path.exists(queuefile):
                os.symlink(dumpdir, queuefile)

