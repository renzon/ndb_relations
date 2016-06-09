# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb
from google.appengine.ext.ndb.model import Model
from google.appengine.ext.ndb.polymodel import PolyModel


class Relation(PolyModel):
    creation = ndb.DateTimeProperty(auto_now_add=True)
    origin = ndb.KeyProperty(required=True)
    destin = ndb.KeyProperty(required=True)

    @classmethod
    def _set_destin_property(cls, model, name, origins):
        setattr(model, name, origins)

    @classmethod
    def _set_origin_property(cls, model, name, destins):
        setattr(model, name, destins)

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
    def _set_destin_property(cls, model, name, origins):
        setattr(model, name, origins[0])

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
            self.model = key_or_model
            self.key = key_or_model.key
        else:
            self.key = key_or_model
            self._model_future = key_or_model.get_async()
            self.model = _ModelNone

    def fetch(self):
        if self.model is _ModelNone:
            self.model = self._model_future.get_result()
        return [self.model]


def fetch(key_or_model, *args):
    fetcher = _ModelAsyncFetcher(key_or_model)
    fetch_mult(fetcher, *args)
    return fetcher.model


def _define_property_and_opposite(cls, key):
    prop = 'origin'
    opposite_prop = 'destin'
    if key.kind() == cls.destin._kind:
        prop = 'destin'
        opposite_prop = 'origin'
    return opposite_prop, prop


class _RelationsSearch(object):
    def __init__(self, prop, opposite_prop, model, name, query, cls):
        self.cls = cls
        self.name = name
        self.model = model
        self.opposite_prop = opposite_prop
        self.prop = prop
        query = query.filter(getattr(cls, prop) == model.key)
        self.relation_futures = query.fetch_async()
        self.opposite_futures = None

    def fetch_obj_futures(self):
        opposite_keys = [getattr(relation, self.opposite_prop) for relation in self.relation_futures.get_result()]
        self.opposite_futures = ndb.get_multi_async(opposite_keys)

    def fetch_final_objs(self):
        method_name = '_set_{}_property'.format(self.prop)
        objs = tuple(f.get_result() for f in self.opposite_futures)
        getattr(self.cls, method_name)(self.model, self.name, objs)
        return objs


def fetch_mult(query, *args):
    models = query.fetch()
    searches = []
    for tpl in args:
        name, query = tpl
        cls = query._relation_cls
        if models:
            opposite_prop, prop = _define_property_and_opposite(cls, models[0].key)
        searches.extend(_RelationsSearch(prop, opposite_prop, m, name, query, cls) for m in models)

    for s in searches:
        s.fetch_obj_futures()
    for s in searches:
        s.fetch_final_objs()

    return models

# Maybe work for sequential
# for tpl in args:
#     name, query = tpl
#     cls = query._relation_cls
#     if current_models:
#         opposite_prop, prop = _define_property_and_opposite(cls, current_models[0].key)
#     searches = tuple(_RelationsSearch(prop, opposite_prop, m, name, query, cls) for m in current_models)
#     for s in searches:
#         s.fetch_obj_futures()
#
#     current_models = tuple(m for m in (s.fetch_final_objs() for s in searches))
