# ndb_relations
Google App Engine (GAE) New Date Base (NDB relations for Humans

Supose an Order refering an User and OrderItems.
More than that, supose you wanna keep reference for items an user have bought or
which users bought some item.

So you have an 1 to n relationship from User to Order and another from Order to OrdemItem.
And you have a n to m relationshipe from User to OrderItem.

Following [NDB docs](https://cloud.google.com/appengine/docs/python/ndb/) you can create an example.py as follows:


```python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from google.appengine.ext import ndb


class User(ndb.Model):
    name = ndb.StringProperty()


class OrderItem(ndb.Model):
    name = ndb.StringProperty()
    price = ndb.FloatProperty()
    order = ndb.KeyProperty(Order)


class Order(ndb.Model):
    user = ndb.KeyProperty(User)


class OrderItemUserLog(ndb.Model):
    item = ndb.KeyProperty(Order)
    user = ndb.KeyProperty(User)
```

So you can create model and connect them using their keys:


```python

# Initializing Testbed to emulate datastore and memcache services
>>> from google.appengine.ext import testbed
>>> t = testbed.Testbed()
>>> t.setup_env(app_id='my-app')
>>> t.activate()
>>> t.init_datastore_v3_stub()
>>> t.init_memcache_stub()

# Creating Models 
>>> from tests.example import *

# Creating User
>>> user = User(name='Renzo')
>>> user.put()
Key('User', 1)

# Creating Order
>>> order = Order(user=user.key)
>>> order.put()
Key('Order', 2)

# Creating Items

>>> items = [OrderItem(name='Tablet', price=12.90, order=order.key), OrderItem(name='Computer', price=22.80, order=order.key)]
>>> from google.appengine.ext import ndb
>>> ndb.put_multi(items)
[Key('OrderItem', 3), Key('OrderItem', 4)]

# Creating n to m connection from user to item
>>> logs = [OrderItemUserLog(user=user.key, item=item.key) for item in items]
>>> ndb.put_multi(logs)
[Key('OrderItemUserLog', 6), Key('OrderItemUserLog', 5)]
```

