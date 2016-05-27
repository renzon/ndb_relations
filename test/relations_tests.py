# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from test.example_using_relations import User, Order, OrderOwner
from test.util import GAETestCase


class FetchTests(GAETestCase):
    def setUp(self):
        super(FetchTests, self).setUp()

        self.user = User(name='Renzo')
        user_key = self.user.put()
        self.order = Order()
        order_key = self.order.put()

        OrderOwner(origin=user_key, destin=order_key).put()

    def test_fetch_user_with_key(self):
        order = OrderOwner.fetch(self.order.key, ('user', OrderOwner.query()))
        self.assertEqual(order, self.order)
        self.assertEqual(order.user, self.user)
