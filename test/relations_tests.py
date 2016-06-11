# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb
from google.appengine.ext import testbed

import pytest
from ndb_relations.relations import OneToManyViolation, fetch, fetch_mult
from test.example_using_relations import User2, Order2, OrderOwner, OrderItemRelation, Item


def assert_same_models(left, right):
    assert len(left) == len(right)
    assert set(e.key for e in left) == set(e.key for e in right)


@pytest.yield_fixture(autouse=True)
def appengine():
    tb = testbed.Testbed()
    tb.setup_env(app_id="_")
    tb.activate()
    tb.init_datastore_v3_stub()
    tb.init_user_stub()
    tb.init_urlfetch_stub()
    tb.init_memcache_stub()
    tb.init_mail_stub()
    tb.init_taskqueue_stub()
    yield None

    tb.deactivate()


@pytest.fixture
def user():
    us = User2(name='Renzo')
    us.put()
    return us


@pytest.fixture
def orders(user):
    user_key = user.key
    ords = (Order2(), Order2())
    order_keys = ndb.put_multi(ords)

    ndb.put_multi([OrderOwner(origin=user_key, destin=order_key) for order_key in order_keys])
    return ords


@pytest.fixture
def items(orders):
    order_keys = [o.key for o in orders]
    its = (Item(name='Notebook'), Item(name='Tablet'))
    item_keys = ndb.put_multi(its)
    ndb.put_multi([OrderItemRelation(origin=order_keys[0], destin=item_key) for item_key in item_keys])
    return its


def test_fetch_user_with_key(user, orders):
    q = OrderOwner.query()
    q.fetch()
    order = fetch(orders[0].key, ('user', OrderOwner.query()))
    assert order == orders[0]
    assert order.user == user


def test_fetch_orders_with_key(user, orders):
    user_from_fetch = fetch(user.key, ('orders', OrderOwner.query()))
    assert user == user_from_fetch
    assert_same_models(orders, user_from_fetch.orders)


def test_fetch_order_with_items_and_owner(user, orders, items):
    order = orders[0]
    order = fetch(order.key, ('user', OrderOwner.query()), ('items', OrderItemRelation.query()))
    assert order.user == user
    assert_same_models(items, order.items)


def test_one_to_many_violation(orders):
    another_user_key = User2(name='John').put()
    order_owner = OrderOwner(origin=another_user_key, destin=orders[0].key)
    with pytest.raises(OneToManyViolation):
        order_owner.put()


@pytest.fixture
def other_items(orders):
    items_2 = [Item(name='Cellphone'), Item(name='Printer')]
    item_2_keys = ndb.put_multi(items_2)
    ndb.put_multi([OrderItemRelation(origin=orders[1].key, destin=item_key) for item_key in item_2_keys])
    return items_2


def test_usual_fetch_multi(orders, items, other_items):
    orders_fetch = fetch_mult(Order2.query(), ('items', OrderItemRelation.query()))
    assert_same_models(orders, orders_fetch)
    assert_same_models(items, orders[0].items)
    assert_same_models(other_items, orders[1].items)
