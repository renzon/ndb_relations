# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb


class User(ndb.Model):
    name = ndb.StringProperty()


class Order(ndb.Model):
    user = ndb.KeyProperty(User)


class OrderItem(ndb.Model):
    name = ndb.StringProperty()
    price = ndb.FloatProperty()
    order = ndb.KeyProperty(Order)


class OrderItemUserLog(ndb.Model):
    item = ndb.KeyProperty(OrderItem)
    user = ndb.KeyProperty(User)
