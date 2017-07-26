import os
import sys
import logging

_sys_path = sys.path
_root_path = os.path.dirname(__file__)

for i in os.listdir(_root_path):
    path = os.path.join(_root_path, i)
    if (os.path.isdir(path)):
        sys.path = _sys_path + [os.path.join('.', path)]
        try:
            from aclient import *
            logging.debug('use %s blobs' % path)
            _sys_path = None
            break
        except Exception, e:
            logging.debug('skip %s blobs: %s' % (path, e))

if _sys_path:
    raise('cannot find proper binary blobs')
