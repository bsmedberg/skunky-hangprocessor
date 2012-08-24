# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import web
import os
import datetime
import uuid
import json
from config import getconfig

config = None

urls = (
  '/', 'goaway',
  '/submit', 'submit'
)

def makeuuid(d):
    u = uuid.uuid4()
    return 'hr-%s-%s' % (d.strftime('%Y%m%d'), u)

class goaway(object):
    @staticmethod
    def GET():
        web.notfound()
        return '<head><title>Wrong server</title><body><p>This is not the droid you are looking for. Perhaps <a href="http://crash-stats.mozilla.com/">crash-stats.mozilla.com</a> is what you wanted?'

class submit(object):
    def GET(self):
        if not config.collector_expose_testform:
            return goaway.GET()

        return """<!DOCTYPE html>
<head>
  <title>Minidump Upload</title>
<body>
  <form action="" method="POST" enctype="multipart/form-data">
    <input type="hidden" name="hiddentest" value="Isunicode?">
    <input type="hidden" name="additional_minidumps" value="browser,flashsandbox">
    <p>Plugin&nbsp;minidump:&nbsp;<input type="file" name="upload_file_minidump">
    <br>Browser&nbsp;minidump:&nbsp;<input type="file" name="upload_file_minidump_browser">
    <br>Flash&nbsp;(sandbox)&nbsp;minidump:&nbsp;<input type="file" name="upload_file_minidump_flashsandbox">
    
    <p><input type="submit" value="Submit...">
  </form>"""

    @staticmethod
    def writefiles(dumpdir, dumpmap, theform):
        if os.path.exists(dumpdir):
            raise Exception("Whoa nellie, UUID collisions are unexpected")

        os.makedirs(dumpdir)
        
        for name, data in dumpmap.items():
            dump = os.path.join(dumpdir, 'minidump_%s.dmp' % name)
            fd = open(dump, 'wb')
            fd.write(data)
            fd.close()

        jsonpath = os.path.join(dumpdir, 'extra.json')
        fd = open(jsonpath, 'wb')
        json.dump(theform, fd)
        fd.close()

    def POST(self):
        t = datetime.datetime.utcnow()
        theform = web.input()

        dumpmap = {'plugin': theform['upload_file_minidump']}
        if 'additional_minidumps' in theform:
            extras = theform.additional_minidumps.split(',')
            for extra in extras:
                dumpmap[extra] = theform['upload_file_minidump_%s' % extra]
                
        for (key, value) in web.webapi.rawinput().iteritems():
            if hasattr(value, 'file') and hasattr(value, 'value'):
                del theform[key]

        crashid = makeuuid(t)
        dumpdir = os.path.join(config.minidump_storage_path, str(t.year),
                               t.strftime('%m-%d'), crashid)
        queueitempath = os.path.join(config.processor_queue_path, crashid)

        try:
            self.writefiles(dumpdir, dumpmap, theform)
            os.symlink(dumpdir, queueitempath)
        except:
            shutil.rmtree(dumpdir, ignore_errors=True)
            raise web.webapi.InternalError("I/O error")

        return "CrashID=%s" % crashid

def getapp():
    return web.application(urls, globals())

if __name__ == '__main__':
    config = getconfig()
    app = getapp()
    web.httpserver.runsimple(app.wsgifunc(),
                             (config.collector_addr, config.collector_port))
