# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb
from google.appengine.ext.ndb.polymodel import PolyModel


class Relation(PolyModel):
    creation = ndb.DateTimeProperty(auto_now_add=True)
    origin = ndb.KeyProperty(required=True)
    destin = ndb.KeyProperty(required=True)

    @classmethod
    def fetch(cls, key, *args):
        model_future = key.get_async()
        if args:
            name, query = args[0]
            query.filter(cls.destin == key)
            origin_keys = [relation.origin for relation in query.fetch()]
            origin_futures = ndb.get_multi_async(origin_keys)
            model = model_future.get_result()
            cls._set_relation_property(model, name, origin_futures)
            return model

        return model_future.get_result()

    @classmethod
    def _set_relation_property(cls, model, name, origin_futures):
        setattr(model, name, [f.get_result() for f in origin_futures])


class OneToMany(Relation):
    @classmethod
    def _set_relation_property(cls, model, name, origin_futures):
        setattr(model, name, origin_futures[0].get_result())
