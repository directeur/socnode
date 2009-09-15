# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import permalink, signals
from google.appengine.ext import db
from django.core.urlresolvers import reverse
from subscriptions.signals import post_subscribe, pre_unsubscribe
from network.pings import subscribe_ping

class Subscription(db.Model):
    """A basic subscription"""
    subscribers = db.ListProperty(db.Key)
    is_service = db.BooleanProperty(default=False)
    url = db.StringProperty()
    feed_id = db.StringProperty()
    feed_url = db.StringProperty()
    title = db.StringProperty()
    etag = db.TextProperty()
    hub = db.StringProperty()
    verified = db.BooleanProperty(default=False)
    updated = db.DateTimeProperty(auto_now=True)

    def __unicode__(self):
        return '%s on hub %s' % (self.feed_url, self.hub)
    
    @permalink
    def get_callback_url(self):
        return ('subscriptions.views.subscribe_callback', [str(self.key())])

    @property
    def owners(self):
         return db.get(self.subscribers)

# signal: everytime a subscription is saved, look if it's associated with a hub
# and subscribe to that hub. and on delete: unsubscribe from hub, if any.

def subscribe_to_hub(sender, **kwargs):
    instance = kwargs['instance']
    created = kwargs['created']
    host = kwargs['host']
    mode = 'subscribe'
    verify = 'sync'
    topic = instance.feed_url
    hub_url = instance.hub
    callback = '%s%s' % (host, instance.get_callback_url())
    if created and hub_url:
        logging.info('pinged %s for subscription on %s callback %s' % (hub_url,
            topic, callback))
        subscribe_ping(hub_url, mode, callback, topic, verify)

def unsubscribe_from_hub(sender, **kwargs):
    instance = kwargs['instance']
    host = kwargs['host']
    mode = 'unsubscribe'
    verify = 'sync'
    topic = instance.feed_url
    hub_url = instance.hub
    callback = '%s%s' % (host, instance.get_callback_url())
    logging.info('pinged %s for subscription on %s callback %s' % (hub_url,
        topic, callback))
    if hub_url:
        subscribe_ping(hub_url, mode, callback, topic, verify)

# connect signals on subscriptions creation and deletion
post_subscribe.connect(subscribe_to_hub)
pre_unsubscribe.connect(unsubscribe_from_hub)
