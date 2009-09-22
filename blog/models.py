# -*- coding: utf-8 -*-
import logging
import hashlib
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.db.models import permalink, signals
from django.template.defaultfilters import slugify
from google.appengine.ext import db
from subscriptions.models import Subscription
from network.pings import publish_ping
from network.utils import memoize
from blog.signals import post_publish

class EntryManager(models.Manager):

    @memoize('/entries/latest_%s_%s')
    def latest(self, username='', friends=False):
        """
        get entries ordered by update date.
        username = '' => all entries
        username != '' and not Friends = > entries by username
        username != '' and Friends = > entries by username and friends

        """
        if friends:
            entries =  Entry.all().filter('subscribers_usernames = ',
                username).order('-updated')
        else:
            if username:
                user = User.all().filter('username = ', username).get()
                if user is None: return []
                else:
                    entries =  Entry.all().filter('owner = ', user).\
                            order('-updated')
            else:
                entries =  Entry.all().order('-updated')
        return entries

    def get_by_id(self, id):
        """get entry by its entry_id (Atom ID, that is)"""
        return  Entry.all().filter('entry_id = ', id).get()
       

class Entry(db.Model):
    """
    A basic entry
    The author may be different from the owner in the scenario where the entry
    comes from a subscription that belongs to the owner.
    """
    subscription = db.ReferenceProperty(Subscription)
    owner = db.ReferenceProperty(User)
    subscribers_usernames = db.StringListProperty()
    author = db.StringProperty()
    author_url = db.StringProperty()
    link = db.StringProperty()
    source = db.StringProperty()
    body = db.TextProperty(required=True)
    entry_id =  db.StringProperty()
    published = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

    objects = EntryManager()

    class Meta:
        ordering = ('-updated',)
        verbose_name_plural = 'entries'

    def get_published_zulu_time(self):
        return self.published.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_updated_zulu_time(self):
        return self.updated.strftime("%Y-%m-%dT%H:%M:%SZ")

    def __unicode__(self):
        return '%s : %s' % (self.author, self.title)

    def _get_slug(self):
        return slugify(self.title)

    slug = property(_get_slug)

    @permalink
    def get_absolute_url(self):
        return ('blog.views.show_entry', (), {'key': self.key()})

    def save(self):
        #why? Well, maybe we'll want to add filters or something, anyway it
        #doesn't hurt for now :)
        super(Entry, self).put()


def publish_to_hub(sender, **kwargs):
    username = kwargs['username']
    host = kwargs['host']
    author_feed_url = host+'/feed/'+username
    foaf_feed_url = host+'/feed/friends/'+username
    hub_url = getattr(settings, 'HUB', 'http://pubsubhubbub.appspot.com')
    logging.info('pinged %s for publishing event on %s' % (hub_url, author_feed_url))
    publish_ping(hub_url, author_feed_url)
    logging.info('pinged %s for publishing event on %s' % (hub_url, foaf_feed_url))
    publish_ping(hub_url, foaf_feed_url)

# signal: Everytime an entry is saved, ping our hub. settings['HUB']
post_publish.connect(publish_to_hub)
