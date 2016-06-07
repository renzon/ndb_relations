# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from functools import partial

from google.appengine.ext import ndb
from google.appengine.ext.ndb.model import Model
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
    if isinstance(key, Model):
        model = key
        key = model.key
    else:
        model_future = key.get_async()
        model = None

    partials = []

    for tpl in args:
        name, query = tpl
        cls = query._relation_cls
        opposite_prop, prop = _define_property_and_opposite(cls, key)
        query = query.filter(getattr(cls, prop) == key)
        relation_futures = query.fetch_async()
        opposite_keys = [getattr(relation, opposite_prop) for relation in relation_futures.get_result()]
        opposite_futures = ndb.get_multi_async(opposite_keys)
        model = model or model_future.get_result()
        method_name = '_set_{}_property'.format(prop)
        p = partial(getattr(cls, method_name), model, name, opposite_futures)

        partials.append(p)

    for p in partials:
        p()

    return model or model_future.get_result()


def _define_property_and_opposite(cls, key):
    prop = 'origin'
    opposite_prop = 'destin'
    if key.kind() == cls.destin._kind:
        prop = 'destin'
        opposite_prop = 'origin'
    return opposite_prop, prop


def fetch_mult(query, *args):
    models = query.fetch()
    for m in models:
        fetch(m, *args)
    return models
