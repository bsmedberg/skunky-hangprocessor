# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import cherrypy
import os
import datetime
import uuid
import json
from config import getconfig
import cgi
import tempfile
import shutil

def makeuuid(d):
    u = uuid.uuid4()
    return 'hr-%s-%s' % (d.strftime('%Y%m%d'), u)

class Collector(object):
    def __init__(self, config):
        self.config = config

    @cherrypy.expose
    def index(self):
        if not config.collector_expose_testform:
            cherrypy.HTTPError(404).set_response()
            return '<head><title>Wrong server</title><body><p>This is not the droid you are looking for. Perhaps <a href="http://crash-stats.mozilla.com/">crash-stats.mozilla.com</a> is what you wanted?'

        return """<!DOCTYPE html>
<head>
  <title>Minidump Upload</title>
<body>
  <form action="submit" method="POST" enctype="multipart/form-data">
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
        
        for name, fs in dumpmap.items():
            dump = os.path.join(dumpdir, 'minidump_%s.dmp' % name)
            outfd = open(dump, 'wb')
            shutil.copyfileobj(fs.file, outfd)
            outfd.close()

        jsonpath = os.path.join(dumpdir, 'extra.json')
        fd = open(jsonpath, 'wb')
        json.dump(theform, fd)
        fd.close()

    @cherrypy.expose
    def submit(self, **kwargs):
        # Note: GET and POST args are mixed in kwargs. body.params contains
        # only the POST fields.
        if cherrypy.request.method.upper() != 'POST':
            raise cherrypy.HTTPRedirect(cherrypy.url('/'))

        theform = dict(cherrypy.request.body.params)

        t = datetime.datetime.utcnow()

        dumpmap = {'plugin': theform['upload_file_minidump']}
        if 'additional_minidumps' in theform:
            extras = theform['additional_minidumps'].split(',')
            for extra in extras:
                dumpmap[extra] = theform['upload_file_minidump_%s' % extra]
                
        for (key, value) in theform.items():
            if hasattr(value, 'file'):
                del theform[key]

        theform['submitted_timestamp'] = t.isoformat()

        crashid = makeuuid(t)
        dumpdir = os.path.join(config.minidump_storage_path, str(t.year),
                               t.strftime('%m-%d'), crashid)
        queueitempath = os.path.join(config.processor_queue_path, crashid)

        try:
            self.writefiles(dumpdir, dumpmap, theform)
            os.symlink(dumpdir, queueitempath)
        except:
            shutil.rmtree(dumpdir, ignore_errors=True)
            raise

        return "CrashID=%s" % crashid

if __name__ == '__main__':
    config = getconfig()
    app = Collector(config)
    cherryconfig = {'global': {'server.socket_host': config.collector_addr,
                               'server.socket_port': config.collector_port}}
    cherrypy.quickstart(app, config=cherryconfig)
