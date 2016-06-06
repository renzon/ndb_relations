# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb

from ndb_relations.relations import OneToMany


class User2(ndb.Model):
    name = ndb.StringProperty()


class Order2(ndb.Model):
    pass


class OrderItem2(ndb.Model):
    name = ndb.StringProperty()
    price = ndb.FloatProperty()


class OrderOwner(OneToMany):
    origin = ndb.KeyProperty(User2)
    destin = ndb.KeyProperty(Order2)


class Item(ndb.Model):
    name = ndb.StringProperty()

class OrderItemRelation(OneToMany):
    origin = ndb.KeyProperty(Order2)
    destin = ndb.KeyProperty(Item)
