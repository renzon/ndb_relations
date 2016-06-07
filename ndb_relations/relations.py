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


class _ModelNone(object):
    pass


class _ModelAsyncFetcher(object):
    def __init__(self, key_or_model):
        if isinstance(key_or_model, Model):
            self._model = key_or_model
            self.key = key_or_model.key
        else:
            self.key = key_or_model
            self._model_future = key_or_model.get_async()
            self._model = _ModelNone

    @property
    def model(self):
        if self._model is _ModelNone:
            self._model = self._model_future.get_result()
        return self._model


def fetch(key_or_model, *args):
    partials = []
    model_fetcher = _ModelAsyncFetcher(key_or_model)

    for tpl in args:
        name, query = tpl
        cls = query._relation_cls
        opposite_prop, prop = _define_property_and_opposite(cls, model_fetcher.key)
        query = query.filter(getattr(cls, prop) == model_fetcher.key)
        relation_futures = query.fetch_async()
        opposite_keys = [getattr(relation, opposite_prop) for relation in relation_futures.get_result()]
        opposite_futures = ndb.get_multi_async(opposite_keys)
        method_name = '_set_{}_property'.format(prop)
        p = partial(getattr(cls, method_name), model_fetcher.model, name, opposite_futures)

        partials.append(p)

    for p in partials:
        p()

    return model_fetcher.model


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
