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

>>> items = [OrderItem(name='Tablet', price=12.90, order=order.key),
...          OrderItem(name='Computer', price=22.80, order=order.key)]
>>> from google.appengine.ext import ndb
>>> ndb.put_multi(items)
[Key('OrderItem', 3), Key('OrderItem', 4)]

# Creating n to m connection from user to item
>>> logs = [OrderItemUserLog(user=user.key, item=item.key) for item in items]
>>> ndb.put_multi(logs)
[Key('OrderItemUserLog', 6), Key('OrderItemUserLog', 5)]
```

Some, after entities creation you want retrieve data. Let's say you have Order id and want retrieve it's user and items:

```python

>>> order=ndb.Key(Order,2).get()
>>> order
Order(key=Key('Order', 2), user=Key('User', 1))
>>> order.user_from_db = order.user.get()
>>> order.user_from_db
User(key=Key('User', 1), name=u'Renzo')
>>> order.items = OrderItem.query(OrderItem.order == order.key).fetch()
>>> order.items
[OrderItem(key=Key('OrderItem', 3), name=u'Tablet', order=Key('Order', 2), price=12.9), OrderItem(key=Key('OrderItem', 4), name=u'Computer', order=Key('Order', 2), price=22.8)]
```

This code works fine but it has some drawbacks:

1) You have to write the entire code yourself
2) It is running serially and could be parallel

To solve 2, you could use async option from ndb itself:

```python
>>> user_future = order.user.get_async()
>>> items_future = OrderItem.query(OrderItem.order==order.key).fetch_async()
>>> user_future.get_result()
User(key=Key('User', 1), name=u'Renzo')
>>> items_future.get_result()
[OrderItem(key=Key('OrderItem', 3), name=u'Tablet', order=Key('Order', 2), price=12.9), OrderItem(key=Key('OrderItem', 4), name=u'Computer', order=Key('Order', 2), price=22.8)]
```

But you would still have to write code and it grows with you want get more connections.
The boilerp,ate code get worse for n to m relations. Let's retrieve a user's items:

```python
>>> logs = OrderItemUserLog.query(OrderItemUserLog.user == ndb.Key(User, 1)).fetch()
>>> logs
[OrderItemUserLog(key=Key('OrderItemUserLog', 5), item=Key('OrderItem', 4), user=Key('User', 1)), 
 OrderItemUserLog(key=Key('OrderItemUserLog', 6), item=Key('OrderItem', 3), user=Key('User', 1))]
>>> item_keys=[lg.item for lg in logs]
>>> item_keys
[Key('OrderItem', 4), Key('OrderItem', 3)]
>>> items = ndb.get_multi(item_keys)
>>> items
[OrderItem(key=Key('OrderItem', 4), name=u'Computer', order=Key('Order', 2), price=22.8), 
 OrderItem(key=Key('OrderItem', 3), name=u'Tablet', order=Key('Order', 2), price=12.9)]
```

So here you have to manually retrieve item keys from the relationship and retrieve respective entities from DB.

This is too much code for people used to ORM's on SQL Data Bases, like Django's ORM.

To solve this problem this lib provide a way to make relationships differently.

## Defining a Relationship

Let's define a relationship between order and user:

```python
from ndb_relations.relations import Relation, OneToManyMixin
from tests.example_using_relations import Order, User

class OrderOwner(Relation, OneToManyMixin):
    origin = ndb.KeyProperty(User)
    destin = ndb.KeyProperty(Order)
```

So to retrieve the order its ownner:

```python
# Creating relation
>>> from example_using_relations import Order, OrderOwner
>>> OrderOwner(origin=user.key, destin=order.key).put()
Key('OrderOwner', 2)

# Fetching Order with User
>>> from google.appengine.ext import ndb
>>> order_key = ndb.Key(Order, 2)
>>> from ndb_relations import relations
>>> relations.fetch(order_key, ('user', OrderOwner))
Order(key=Key('Order', 7))
>>> order.user
User(key=Key('User', 1), name=u'Renzo')

# Fetching User with Orders
>>> user_key = ndb.Key(User, 1)
>>> user = relations.fetch(user_key, ('orders', OrderOwner))
>>> user
User(key=Key('User', 1), name=u'Renzo')
>>> user.orders
[Order(key=Key('Order', 7))]
``



