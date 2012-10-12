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
            if config.collector_root_redirect != '':
                raise cherrypy.HTTPRedirect(config.collector_root_redirect)
            cherrypy.response.status = 404
            return '<head><title>Wrong server</title><link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAArhJREFUeNqUU19IU1Ec/jY3ZLrN1JBCAyUfphBaQpCYUGkPitmDFEoUWPZSGf55EXsLM0QopbdW9KBEEGQoFkX1YBY41BSRpS3TXd0Y2+62O7e73etO59w226SXPjjnd8/5fffjO7/zOyr8A3WNTWNiMNAoiiKi0QjEiGxeWpxt28sjhEDNPm51dJPkRDiW3njhynXUNjShyFSObTntWnI+ma9hk+AP7CYHz6BXEkZdfvNonobSSlXA8YNwqfPR2/UefXv5Kjadb7pIYjE1qrzPrbn7YSou0MKgI7sEQVRh1S7B44b1c06zSa2OYezlCxU7guJgbW29p86w0F914oCpIH8f5B12PjriAll0KiwGOI438V9fYVIo70lxQJE9UA1ve9clxPTZkIMOECn016Y2AxpdLuSwBPPwU3R+QA7d5hUHl1vbrkaRbo6tPgI3MQIxcx+MpaehyyuGhvmLAQGHHV7ra2xzTkgS0Nx606tFhBX2iUav15t5ITJOxRqMZ2/jcNlRzD8bhLxsQZizI7voECRtFo51PMSPT1+Ax8NQkdi43qA3MwHmsIKOwv6TID+H6ok0N0jm+moI2Rghb89BiZa7NWRnfoDM3Ksn96uV0hSy/xJFnGUq6jRabYcNwlYu/Js2RO3fEJahRN5uQ4BbBM/ZFB7Fr/j400hKQ6ghOJ1OBB3LCPIeKmZFhN5GkEbB50HQaYXb5VR4yU2lCJyqrW+x4AhZ2vBR4iqikoyQ1wWJFjDEuxCJyPBw37Hl9WGG8hg/RcCQqRv1GcuMDyyonpzyi2t8CO6NBezQS3avL2AzGMKbKUEconmfoczI+CkCRqMB3PpKCydguvsdKq0+3JmYjqw4qYNxGlfouucjKlme8Rg/BTfaO1llM5K2WKOUxG+oJL5OICPOV15jAhX4P1QkBH4LMADYK1S5qnGrYAAAAABJRU5ErkJggg==" rel="icon"><body><p>This is not the droid you are looking for. Perhaps <a href="http://crash-stats.mozilla.com/">crash-stats.mozilla.com</a> is what you wanted?'

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

        # Cherrypy 3.1 compat
        if hasattr(cherrypy.request.body, 'params'):
            theform = dict(cherrypy.request.body.params)
        else:
            theform = dict(cherrypy.request.body_params)

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

        return "CrashID=bp-%s" % crashid

if __name__ == '__main__':
    config = getconfig()
    app = Collector(config)
    cherryconfig = {'global': {'server.socket_host': config.collector_addr,
                               'server.socket_port': config.collector_port,
                               'engine.autoreload.on': False,
                               'log.screen': False,
                               'log.access_file': config.collector_access_log,
                               'log.error_file': config.collector_error_log}}
    cherrypy.quickstart(app, config=cherryconfig)
