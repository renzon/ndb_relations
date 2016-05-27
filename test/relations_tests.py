# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb

from ndb_relations.relations import OneToManyViolation
from test.example_using_relations import User, Order, OrderOwner
from test.util import GAETestCase


class FetchTests(GAETestCase):
    def setUp(self):
        super(FetchTests, self).setUp()

        self.user = User(name='Renzo')
        user_key = self.user.put()
        self.orders = [Order(), Order()]
        order_keys = ndb.put_multi(self.orders)

        ndb.put_multi([OrderOwner(origin=user_key, destin=order_key) for order_key in order_keys])

    def test_fetch_user_with_key(self):
        order = OrderOwner.fetch(self.orders[0].key, ('user', OrderOwner.query()))
        self.assertEqual(order, self.orders[0])
        self.assertEqual(order.user, self.user)

    def test_fetch_orders_with_key(self):
        user = OrderOwner.fetch(self.user.key, ('orders', OrderOwner.query()))
        self.assertEqual(user, self.user)
        self.assertEqual(user.orders, self.orders)

    def test_one_to_many_violation(self):
        another_user_key = User(name='John').put()
        order_owner=OrderOwner(origin=another_user_key, destin=self.orders[0].key)
        self.assertRaises(OneToManyViolation, order_owner.put)
