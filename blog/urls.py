# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('blog.views',
    (r'^create_admin_user$', 'create_admin_user'),
    (r'^$', 'list_all_entries'),
    (r'^create$', 'add_entry'),
    (r'^show/(?P<key>.+)$', 'show_entry'),
    (r'^edit/(?P<key>.+)$', 'edit_entry'),
    (r'^delete/(?P<key>.+)$', 'delete_entry'),
    #feeds
    (r'^feed/$', 'everyone_feed'),
    (r'^feed/friends/(?P<username>.+)$', 'foaf_feed'),
    (r'^feed/(?P<username>.+)$', 'author_feed'),
    #json
    (r'^json/(?P<username>.+)$', 'json_author_entries'),
    #entries
    (r'^friends/(?P<username>.+)$', 'show_foaf_entries'),
    (r'^(?P<username>.+)$', 'show_author_entries'),
)
