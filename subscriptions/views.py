# -*- coding: utf-8 -*-
import logging
import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from google.appengine.ext import db
from mimetypes import guess_type
from subscriptions.models import Subscription
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect
from network.parsers import url_to_subscription, DataFeed
from blog.models import Entry
from blog.signals import post_publish
from subscriptions.signals import post_subscribe, pre_unsubscribe

try:
    from google.appengine.api import taskqueue
except ImportError:
    from google.appengine.api.labs import taskqueue

@login_required
def list_subscriptions(request):
    kind = request.GET.get("kind", 'friend')
    his_subscriptions = Subscription.all().filter('subscribers = ',
            request.user.key())
    if kind == 'service':
        his_subscriptions.filter('is_service = ', True)
    elif kind == 'friend':
        his_subscriptions.filter('is_service = ', False)
    extra_context = {'kind': kind}
    return object_list(request, his_subscriptions, paginate_by=10,
            extra_context=extra_context)

@login_required
def add_subscription(request):
    """
    This is complicated. (tm)
    A subscription can be:
    1) A user's service: The subscription has to be created if it doesn't exist
    before and the user will be its owner (only subscriber)
    2) A socnode feed: in this case, create the subscription only if it doesn't
    exist before and append the user to its subscribers.
    """
    host = 'http://%s' % request.get_host()
    if request.method == 'POST':
        surl = request.POST.get('surl', '')
        is_service = request.POST.get('is_service', '0')
        subscription_kind = 'service' if is_service=='1' else 'friend'
        subscription =  url_to_subscription(surl)
        if subscription:
            hub = subscription.hub
            subscription.is_service = True if is_service=='1' else False
            msg = '%s is on %s' % (surl, hub)
            # is there any similar subscription?
            similar = Subscription.all().filter('feed_url = ', subscription.feed_url)
            if similar and not subscription.is_service:
                subscription = similar[0]
                created = False
            else:
                created = True
            subscription.subscribers.append(request.user.key())
            subscription.save()
            post_subscribe.send(sender=Subscription, instance=subscription, 
                host=host, created=created)
        else:
            msg = '%s is not a valid feed url' % surl
        return HttpResponseRedirect('/subscriptions/?kind=%s' %
                subscription_kind)

@login_required
def delete_subscription(request, key):
    host = 'http://%s' % request.get_host()
    subscription = db.get(db.Key(key))
    if not subscription:
        raise Http404
    subscription_kind = 'service' if subscription.is_service=='1' else 'friend'
    subscription.subscribers.remove(request.user.key())
    if not subscription.subscribers:
        pre_unsubscribe.send(sender=Subscription, instance=subscription, 
                host=host)
        subscription.delete()
    else:
        subscription.save()
    return HttpResponseRedirect('/subscriptions/?kind=%s' % subscription_kind)

def save_feed_entries(subscription, entries, host):
    """
    Save recieved entries for a given subscription
    - this compares the entry's source with host
    if they're similar, don't save that entry.
    """    
    if subscription is None:
        return False
    if subscription.is_service:
        the_author = subscription.owners[0].username
        the_owner = subscription.owners[0]
    # here the fun begins: parse that feed and create entries!
    for entry in entries:
        entry.subscription = subscription
        entry.subscribers_usernames = [s.username for s in
                subscription.owners]
        if entry.subscription.is_service:
            entry.author = the_author
            entry.owner = the_owner
            entry.author_url = host+'/'+the_author
        #avoid the Ouroboros bug
        logging.info('entry id is %s' % entry.entry_id)
        if not entry.source.startswith(host):
            #is there an entry with the same id? The Lernaean Hydra bug
            old = Entry.objects.get_by_id(entry.entry_id)
            if old is not None:
                logging.info('entry already exists %s' % entry.entry_id)
                old.body = entry.body
                old.link = entry.link
                old.save()
            else:
                entry.save()
    # inform the hub -Todo: Try do it after confirming to the HUB that the
    # entries were recieved. i.e. the last HttpResponse
    # THINK: of tasks
    if entries:
        for subscriber in subscription.owners:
            post_publish.send(sender=Subscription, username=subscriber.username,
                    host=host)
    # thank the hub
    return True

def subscribe_callback(request, key):
    """
    handles both subscription verification from the hub and the processing of
    entries coming from a feed sent by the hub.
    Difference: GET is used for verification and POST is used for pushing the
    feed.
    """
    host = 'http://%s' % request.get_host()
    if request.method == 'GET':
        # just confirm everything for now. nexttime, use verify_token and update
        # the subscription entity.
        hub_challenge = request.GET.get('hub.challenge', '')
        subscription = db.get(db.Key(key))
        if subscription is None: 
            logging.error('CALLBACK:can not find that subscription %s' % key)
            raise Http404
        else:
            subscription.verified = True
            subscription.save()
        return HttpResponse(hub_challenge)
    else:
        feed_body = request.raw_post_data
        subscription = db.get(db.Key(key))
        if subscription:
            if subscription.updated:
                modified = subscription.updated.timetuple()
            else:
                modified = None
            #parse the recieved feed body
            feed = DataFeed(feed_body, subscription.etag, modified)
            if feed.parse():
                entries = feed.entries
                subscription.etag = feed.etag
                subscription.updated = datetime.datetime(*feed.modified[:6])
                subscription.save()
            else:
                entries = []
        result = save_feed_entries(subscription, entries, host)
        if result:
            logging.info('HUB:Entries recieved for subscr. %s' % key)
            return HttpResponse('Thanks Hub!')
        else:
            logging.error('HUB:Can not find subscr. %s' % key)
            return HttpResponse('Sorry Hub!')

def subscription_fetch_and_save(request):
    """
    fetch, parse and save entries from a given subscription.
    """
    host = 'http://%s' % request.get_host()
    key = request.POST.get('key')
    logging.info('task run with key %s' % key)
    subscription = db.get(db.Key(key))
    if subscription is None: 
        logging.error('CRON: can not find that subscription %s' % key)
        raise Http404
    else:
        #request latest entries from subscription's feed_url
        if subscription:
            if subscription.updated:
                modified = subscription.updated.timetuple()
            else:
                modified = None
            feed = DataFeed(subscription.feed_url, subscription.etag, modified)
            if feed.parse():
                entries = feed.entries
                subscription.etag = feed.etag
                subscription.updated = datetime.datetime(*feed.modified[:6])
                subscription.save()
            else:
                entries = []
        result = save_feed_entries(subscription, entries, host)
        if result:
            logging.info('CRON:Entries fetched and saved for %s url %s' % (key,
                subscription.feed_url))
            return HttpResponse('Thanks Cron!')
        else:
            logging.error('CRON:Entries NOT saved for %s' % key)
            return HttpResponse('Sorry Cron!')

def cron_job(request):
    """
    fetch subscriptions that aren't connected to a hub.
    """
    nohub_subscriptions = Subscription.all().filter('hub = ', "")
    keys = [str(s.key()) for s in nohub_subscriptions]
    # now launch eftching tasks
    for key in keys:
        logging.info('task set to fetch subscription %s' % key)
        taskqueue.add(url='/subscriptions/fetch_feed/', params={'key': key})
    return HttpResponse('done')
