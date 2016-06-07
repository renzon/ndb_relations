# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb

from ndb_relations.relations import OneToManyViolation, fetch, fetch_mult
from test.example_using_relations import User2, Order2, OrderOwner, OrderItemRelation, Item
from test.util import GAETestCase


def _setup(test_case):
    test_case.user = User2(name='Renzo')
    user_key = test_case.user.put()
    test_case.orders = [Order2(), Order2()]
    order_keys = ndb.put_multi(test_case.orders)

    ndb.put_multi([OrderOwner(origin=user_key, destin=order_key) for order_key in order_keys])

    test_case.items = [Item(name='Notebook'), Item(name='Tablet')]
    item_keys = ndb.put_multi(test_case.items)
    ndb.put_multi([OrderItemRelation(origin=order_keys[0], destin=item_key) for item_key in item_keys])


class FetchTests(GAETestCase):
    def setUp(self):
        super(FetchTests, self).setUp()

        _setup(self)

    def test_fetch_user_with_key(self):
        q = OrderOwner.query()
        q.fetch()
        order = fetch(self.orders[0].key, ('user', OrderOwner.query()))
        self.assertEqual(order, self.orders[0])
        self.assertEqual(order.user, self.user)

    def test_fetch_orders_with_key(self):
        user = fetch(self.user.key, ('orders', OrderOwner.query()))
        self.assertEqual(user, self.user)
        self.assertItemsEqual(user.orders, self.orders)

    def test_fetch_order_with_items_and_owner(self):
        order = self.orders[0]
        order = fetch(order.key, ('user', OrderOwner.query()), ('items', OrderItemRelation.query()))
        self.assertEqual(order.user, self.user)
        self.assertItemsEqual(order.items, self.items)

    def test_one_to_many_violation(self):
        another_user_key = User2(name='John').put()
        order_owner = OrderOwner(origin=another_user_key, destin=self.orders[0].key)
        self.assertRaises(OneToManyViolation, order_owner.put)


class FetchMultTests(GAETestCase):
    def setUp(self):
        super(FetchMultTests, self).setUp()
        _setup(self)

    def test_usual_fetch_multi(self):
        items_2 = [Item(name='Cellphone'), Item(name='Printer')]
        item_2_keys = ndb.put_multi(items_2)
        ndb.put_multi([OrderItemRelation(origin=self.orders[1].key, destin=item_key) for item_key in item_2_keys])
        orders = fetch_mult(Order2.query(), ('items', OrderItemRelation.query()))
        self.assertListEqual(self.orders, orders)
        self.assertItemsEqual(self.items, orders[0].items)
        self.assertItemsEqual(items_2, orders[1].items)
