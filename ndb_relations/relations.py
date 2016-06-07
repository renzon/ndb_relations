# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from functools import partial

from google.appengine.ext import ndb
from google.appengine.ext.ndb.polymodel import PolyModel


class Relation(PolyModel):
    creation = ndb.DateTimeProperty(auto_now_add=True)
    origin = ndb.KeyProperty(required=True)
    destin = ndb.KeyProperty(required=True)

    @classmethod
    def _set_destin_property(cls, model, name, futures):
        setattr(model, name, [f.get_result() for f in futures])

    @classmethod
    def _set_origin_property(cls, model, name, futures):
        setattr(model, name, [f.get_result() for f in futures])

    # It is overwriting the method so it exposes the relation class to fetch function
    @classmethod
    def query(cls, *args, **kwds):
        q = super(Relation, cls).query(*args, **kwds)
        q._relation_cls = cls
        return q


class OneToManyViolation(Exception):
    pass


class OneToMany(Relation):
    @classmethod
    def _set_destin_property(cls, model, name, futures):
        setattr(model, name, futures[0].get_result())

    def _pre_put_hook(self):
        cls = type(self)
        relation = cls.query(cls.destin == self.destin).get(keys_only=True)
        if relation is not None:
            raise OneToManyViolation('{} has already a relation'.format(cls.destin))


def fetch(key, *args):
    model_future = key.get_async()
    model = None
    partials = []

    for tpl in args:
        name, query = tpl
        cls = query._relation_cls

        if key.kind() == cls.origin._kind:
            query.filter(cls.origin == key)
            destin_keys = [relation.destin for relation in query.fetch()]
            destin_futures = ndb.get_multi_async(destin_keys)
            model = model or model_future.get_result()
            p = partial(cls._set_origin_property, model, name, destin_futures)

        else:
            query.filter(cls.destin == key)
            origin_keys = [relation.origin for relation in query.fetch()]
            origin_futures = ndb.get_multi_async(origin_keys)
            model = model or model_future.get_result()
            p = partial(cls._set_destin_property, model, name, origin_futures)

        partials.append(p)

    for p in partials:
        p()

    return model or model_future.get_result()


def fetch_mult(query, *args):
    pass
