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

            if key.kind() == cls.origin._kind:
                query.filter(cls.origin == key)
                destin_keys = [relation.destin for relation in query.fetch()]
                destin_futures = ndb.get_multi_async(destin_keys)
                model = model_future.get_result()
                cls._set_origin_property(model, name, destin_futures)

            else:
                query.filter(cls.destin == key)
                origin_keys = [relation.origin for relation in query.fetch()]
                origin_futures = ndb.get_multi_async(origin_keys)
                model = model_future.get_result()
                cls._set_destin_property(model, name, origin_futures)

            return model

        return model_future.get_result()

    @classmethod
    def _set_destin_property(cls, model, name, futures):
        setattr(model, name, [f.get_result() for f in futures])

    @classmethod
    def _set_origin_property(cls, model, name, futures):
        setattr(model, name, [f.get_result() for f in futures])


class OneToMany(Relation):
    @classmethod
    def _set_destin_property(cls, model, name, futures):
        setattr(model, name, futures[0].get_result())