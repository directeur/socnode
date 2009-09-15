# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('subscriptions.views',
    (r'^$', 'list_subscriptions'),
    (r'^add/$', 'add_subscription'),
    (r'^delete/(?P<key>.+)$', 'delete_subscription'),
    (r'^callback/(?P<key>.+)$', 'subscribe_callback'),
    (r'^fetch_feed/$', 'subscription_fetch_and_save'),
    (r'^cron/$', 'cron_job'),
)
