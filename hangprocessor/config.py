# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from configman import Namespace, ConfigurationManager
import os
import getopt

opts = Namespace()
opts.add_option(
    'minidump_storage_path',
    default='',
    doc='The directory under which minidumps will be collected.'
    )
opts.add_option(
    'processor_queue_path',
    default='',
    doc='The directory in which the processor symlink queue is maintained.'
    )
opts.add_option(
    'minidump_stackwalk_path',
    default='',
    doc='The path of the minidump_stackwalk binary')
opts.add_option(
    'symbol_paths',
    default='',
    doc='A list of paths (separated by os.pathsep, e.g. /foo:/bar on Linux')
opts.add_option(
    'collector_expose_testform',
    default=False,
    doc='Expose an HTML form for testing the collector.')
opts.add_option(
    'collector_addr',
    default='0.0.0.0',
    doc='Address for the collector to bind to.')
opts.add_option(
    'collector_port',
    default=8080,
    doc='Port for the collector to run on.')
opts.add_option(
    'collector_error_log',
    default='/dev/null',
    doc='Absolute path to the collector error log file.')
opts.add_option(
    'collector_access_log',
    default='/dev/null',
    doc='Absolute path to the collector access log file.')
opts.add_option(
    'processor_wakeinterval',
    default=30,
    doc='Wake up every N seconds to process new reports.')
opts.add_option(
    'reporting_server',
    default='',
    doc='Server name which will see the final reports')
opts.add_option(
    'reporting_directory',
    default='',
    doc='Directory on reporting_server which will hold the final reports')

def _validate_single_dir(p, name):
    if not os.path.isabs(p):
        raise Exception("Option '%s' must be an absolute path, got '%s'" % (name, p))
    if not os.path.isdir(p):
        raise Exception("Option '%s' must be a directory, got '%s'" % (name, p))

def _validate_single_executable(p, name):
    if not os.access(p, os.X_OK):
        raise Exception("Option '%s' must be executable, got '%s'" % (name, p))

def _get_dir_list(p, name):
    pl = p.split(os.pathsep)
    for p in pl:
        _validate_single_dir(p, name)

    return pl

def getconfig():
    cm = ConfigurationManager(opts,
                              values_source_list=('/etc/hangprocessor.ini',
                                                  os.path.expanduser('~/hangprocessor.ini'),
                                                  getopt))
    config = cm.get_config()
    
    # Validate the config
    _validate_single_dir(config.minidump_storage_path, 'minidump_storage_path')
    _validate_single_dir(config.processor_queue_path, 'processor_queue_path')
    _validate_single_executable(config.minidump_stackwalk_path, 'minidump_stackwalk_path')
    config.symbol_paths = _get_dir_list(config.symbol_paths, 'symbol_paths')

    return config
