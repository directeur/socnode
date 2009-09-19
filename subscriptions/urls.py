# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('subscriptions.views',
    url(r'^$', 'list_subscriptions', name='list-subscriptions'),
    url(r'^add/$', 'add_subscription', name='add-subscription'),
    url(r'^delete/(?P<key>.+)$', 'delete_subscription', name='delete-subscription'),
    url(r'^callback/(?P<key>.+)$', 'subscribe_callback', name='subscribe-callback'),
    url(r'^fetch_feed/$', 'subscription_fetch_and_save', name='fetch-feed'),
    url(r'^cron/$', 'cron_job', name='cron-job'),
)
