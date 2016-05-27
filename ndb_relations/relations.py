# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb
from google.appengine.ext.ndb.polymodel import PolyModel


class Relation(PolyModel):
    creation = ndb.DateTimeProperty(auto_now_add=True)
    origin = ndb.KeyProperty(required=True)
    destin = ndb.KeyProperty(required=True)

class OneToManyMixin():
    pass