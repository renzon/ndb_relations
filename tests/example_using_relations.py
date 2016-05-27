# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb


class User(ndb.Model):
    name = ndb.StringProperty()


class Order(ndb.Model):
    pass


class OrderItem(ndb.Model):
    name = ndb.StringProperty()
    price = ndb.FloatProperty()
