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
>>> from test.testloader import fix_path
>>> fix_path()
>>> from google.appengine.ext import testbed
>>> t = testbed.Testbed()
>>> t.setup_env(app_id='my-app')
>>> t.activate()
>>> t.init_datastore_v3_stub()
>>> t.init_memcache_stub()

# Creating Models 
>>> from test.example import *

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
[OrderItemUserLog(key=Key('OrderItemUserLog', 5), item=Key('OrderItem', 4), user=Key('User', 1)), OrderItemUserLog(key=Key('OrderItemUserLog', 6), item=Key('OrderItem', 3), user=Key('User', 1))]
>>> item_keys=[lg.item for lg in logs]
>>> item_keys
[Key('OrderItem', 4), Key('OrderItem', 3)]
>>> items = ndb.get_multi(item_keys)
>>> items
[OrderItem(key=Key('OrderItem', 4), name=u'Computer', order=Key('Order', 2), price=22.8), OrderItem(key=Key('OrderItem', 3), name=u'Tablet', order=Key('Order', 2), price=12.9)]

```

So here you have to manually retrieve item keys from the relationship and retrieve respective entities from DB.

This is too much code for people used to ORM's on SQL Data Bases, like Django's ORM.

To solve this problem this lib provide a way to make relationships differently.

## Defining a Relationship

Let's define a relationship between order and user:

```python

from ndb_relations.relations import Relation, OneToManyMixin
from test.example_using_relations import Order2, User2

class OrderOwner(OneToMany):
    origin = ndb.KeyProperty(User2)
    destin = ndb.KeyProperty(Order2)

```

So to fetch the order with its owner:

```python

# Creating Models 
>>> from test.example_using_relations import Order2, OrderOwner, User2 

# Creating User
>>> user = User2(name='Renzo')
>>> user.put()
Key('User2', 7)

# Creating Orders
>>> order = Order2()
>>> order.put()
Key('Order2', 8)
>>> order2 = Order2()
>>> order2.put()
Key('Order2', 9)


# Creating relations
>>> OrderOwner(origin=user.key, destin=order.key).put()
Key('Relation', 10)
>>> OrderOwner(origin=user.key, destin=order2.key).put()
Key('Relation', 11)


# Fetching Order with User
>>> from ndb_relations.relations import fetch
>>> from google.appengine.ext import ndb
>>> order = fetch(order.key, ('user', OrderOwner.query()))
>>> order
Order2(key=Key('Order2', 8))
>>> order.user
User2(key=Key('User2', 7), name=u'Renzo')


# Fetching User with Orders
>>> user = fetch(user.key, ('orders', OrderOwner.query()))
>>> user
User2(key=Key('User2', 7), name=u'Renzo')
>>> user.orders
[Order2(key=Key('Order2', 8)), Order2(key=Key('Order2', 9))]

```

More than that, related object can be found in parallel:

```python
# Creating Models 
>>> from test.example_using_relations import Item, OrderItemRelation
 
>>> item = Item(name='Notebook') 
>>> item.put() 
Key('Item', 12)
>>> item2 = Item(name='Notebook') 
>>> item2.put() 
Key('Item', 13)

# Creating relations
>>> OrderItemRelation(origin=order.key, destin=item.key).put()
Key('Relation', 14)
>>> OrderItemRelation(origin=order.key, destin=item2.key).put()
Key('Relation', 15)

# Order with User and Items
>>> order = fetch(order.key, ('owner', OrderOwner.query()),('items', OrderItemRelation.query()))
>>> order
Order2(key=Key('Order2', 8))
>>> order.owner
User2(key=Key('User2', 7), name=u'Renzo')
>>> order.items
[Item(key=Key('Item', 12), name=u'Notebook'), Item(key=Key('Item', 13), name=u'Notebook')]

```
