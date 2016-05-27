# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import testbed

t = testbed.Testbed()
t.setup_env(app_id='my-app')
t.activate()
t.init_datastore_v3_stub()
t.init_memcache_stub()
