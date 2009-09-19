# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('blog.views',
    url(r'^create_admin_user$', 'create_admin_user', name='create-admin-user'),
    url(r'^$', 'display', {'username':'', 'friends':False}, name='all-entries'),
    url(r'^create$', 'add_entry', name='add-entry'),
    url(r'^show/(?P<key>.+)$', 'show_entry', name='show-entry'),
    url(r'^edit/(?P<key>.+)$', 'edit_entry', name='edit-entry'),
    url(r'^delete/(?P<key>.+)$', 'delete_entry', name='delete-entry'),
    #feeds
    url(r'^feed/$', 'feed', {'username':'', 'friends':False}, name='everyone-feed'),
    url(r'^feed/friends/(?P<username>.+)$', 'feed', {'friends':True}, name='friends-feed'),
    url(r'^feed/(?P<username>.+)$', 'feed', {'friends':False}, name='user-feed'),
    #json
    url(r'^json/$', 'json', {'username':'', 'friends':False}, name='everyone-json'),
    url(r'^json/friends/(?P<username>.+)$', 'json', {'friends':True}, name='friends-json'),
    url(r'^json/(?P<username>.+)$', 'json', {'friends':False}, name='user-json'),
    #entries
    url(r'^friends/(?P<username>.+)$', 'display', {'friends':True}, name='friends-entries'),
    url(r'^(?P<username>.+)$', 'display', {'friends':False}, name='user-entries'),
)
