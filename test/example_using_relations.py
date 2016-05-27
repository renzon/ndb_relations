# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb

from ndb_relations.relations import OneToMany


class User(ndb.Model):
    name = ndb.StringProperty()


class Order(ndb.Model):
    pass


class OrderItem(ndb.Model):
    name = ndb.StringProperty()
    price = ndb.FloatProperty()


class OrderOwner(OneToMany):
    origin = ndb.KeyProperty(User)
    destin = ndb.KeyProperty(Order)


