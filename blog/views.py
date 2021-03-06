# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from google.appengine.ext import db
from mimetypes import guess_type
from blog.forms import EntryForm
from blog.models import Entry
from blog.signals import post_publish
from django.shortcuts import render_to_response, redirect
from network.utils import json_response, forget

MAX_JSON_ENTRIES = getattr(settings, 'MAX_JSON_ENTRIES', 20)
MAX_FEED_ENTRIES = getattr(settings, 'MAX_FEED_ENTRIES', 20)
HUB = getattr(settings, 'HUB', 'http://pubsubhubbub.appspot.com')

def clear_entries_cache(username=''):
    """Clear memacched entries by username"""
    if username:
        forget('/entries/latest%s_%s' % (username, True))
        forget('/entries/latest%s_%s' % (username, False))
    forget('/entries/latest%s_%s' % ('', False))

def display(request, username='', friends=False):
    entries = Entry.objects.latest(username, friends)
    if friends:
        page_title = "Posts by %s and Friends" % username
        feed_title = "%s and Friends Feed" % username
        feed_url = '/feed/friends/'+username,
    else:
        if username:
            user = User.all().filter('username = ', username).get()
            if user is None: raise Http404
            page_title = "Posts by %s" % username
            feed_title = "%s's Feed" % username
            feed_url = '/feed/'+username,
        else:
            page_title = "Home" 
            feed_title = "Everyone's Feed"
            feed_url = '/feed/'

    extra_context = dict(
        page_title = page_title,
        feed_title = feed_title,
        feed_url = feed_url,
        username = username,
    )
    return object_list(request, entries, paginate_by=10,
            extra_context=extra_context)

def feed(request, username='', friends=False):
    host = 'http://%s' % request.get_host()
    entries = Entry.objects.latest(username, friends)[:MAX_FEED_ENTRIES]
    if friends:
        feed_title = "%s and Friends Feed" % username
        source = host+'/feed/friends/'+username
    else:
        if username:
            user = User.all().filter('username = ', username).get()
            if user is None: raise Http404
            feed_title = "%s's Feed" % username
            source = host+'/feed/'+username
        else:
            feed_title = "Everyone's Feed"
            source = host+'/feed/'

    context = dict(
        hub = HUB,
        entries = entries,
        first_entry = entries[0] if entries else None,
        username = username if username else 'Everyone',
        feed_title = feed_title,
        userpage = host+'/'+username,
        source = source
    )
    return render_to_response('atom.xml', context, mimetype="application/atom+xml")

def json(request, username, friends):
    entries = Entry.objects.latest(username, friends)[:MAX_JSON_ENTRIES]
    json_entries = [{
        "key": str(entry.key()),
        "body": entry.body,
        "author": entry.author,
        "author_url": entry.author_url,
        "published": entry.published.isoformat(),
        "updated": entry.updated.isoformat(),
        "link": entry.link,
        "linktext": entry.link,
        "permalink": '/show/'+str(entry.key()),
        "editlink": '/edit/'+str(entry.key()),
        "deletelink": '/delete/'+str(entry.key())
        } for entry in entries]
    json_entries.reverse()
    json = {"entries": json_entries}
    return json_response(json)

def show_entry(request, key):
    return object_detail(request, Entry.all(), key)

@login_required
def add_entry(request):
    host = 'http://%s' % request.get_host()
    if request.method == 'POST': 
        form =EntryForm(request.POST) 
        if form.is_valid():
            entry = form.save(commit=False)
            entry.subscription = None
            entry.owner = request.user
            entry.author = request.user.username
            entry.subscribers_usernames = [request.user.username]
            # let the author_url blank so it won't be hardcoded in the store and
            # in the template, if author_link is empty, generate a link to his
            # entries
            entry.author_url = ''
            entry.save()
            # invalidate cache
            clear_entries_cache(request.user.username)
            # inform the hub
            post_publish.send(sender=Entry, username=entry.author, host=host)
            if request.is_ajax():
                e = dict(
                    author=request.user.username,
                    author_url = host+'/'+request.user.username,
                    body = entry.body,
                    link = entry.link,
                    linktext = entry.link,
                    key = str(entry.key()),
                    permalink = '/show/'+str(entry.key()),
                    editlink = '/edit/'+str(entry.key()),
                    deletelink = '/delete/'+str(entry.key())
                )
                return json_response(e)
            else:
                return HttpResponseRedirect(reverse('user-entries',
                    kwargs={'username': request.user.username})) 
    else:
        form =EntryForm() 

    return render_to_response('entry_form.html', {
        'form': form
    })


@login_required
def edit_entry(request, key):
    host = 'http://%s' % request.get_host()
    entry = db.get(key)
    if entry.author != request.user.username:
        response = HttpResponse('unauthorized') 
        response.status_code = 401 
        return response
    if request.is_ajax():
        body = request.POST.get('body')
        link = request.POST.get('link')
        entry.body = body
        entry.link = link
        entry.save()
        e = dict(
            author=request.user.username,
            author_url = host+'/'+request.user.username,
            body = entry.body,
            link = entry.link,
            linktext = entry.link,
            key = str(entry.key()),
            permalink = '/show/'+str(entry.key()),
            editlink = '/edit/'+str(entry.key()),
            deletelink = '/delete/'+str(entry.key())
        )
        # invalidate cache
        clear_entries_cache(request.user.username)
        # ping hub
        post_publish.send(sender=Entry, username=request.user.username,
                host=host)
        return json_response(e)

    else:
        response = update_object(request, object_id=key, form_class=EntryForm,
                post_save_redirect=reverse('user-entries',
                    kwargs={'username':request.user.username}))
        if isinstance(response, HttpResponseRedirect):
            post_publish.send(sender=Entry, username=request.user.username,
                    host=host)
        return response

@login_required
def delete_entry(request, key):
    entry = db.get(key)
    if entry.author != request.user.username and not request.user.is_superuser:
        response = HttpResponse('unauthorized') 
        response.status_code = 401 
        return response
    # invalidate cache
    clear_entries_cache(request.user.username)
    if request.is_ajax():
        entry.delete()
        r = {
                'key': key,
                'success':True
            }
        return json_response(r)
    else:
        return delete_object(request, Entry, object_id=key,
            post_delete_redirect=reverse('user-entries',
                    kwargs={'username':request.user.username}))

def create_admin_user(request):
    user = User.get_by_key_name('admin')
    if not user or user.username != 'admin' or not (user.is_active and
            user.is_staff and user.is_superuser and
            user.check_password('admin')):
        user = User(key_name='admin', username='admin',
            email='admin@localhost', first_name='Boss', last_name='Admin',
            is_active=True, is_staff=True, is_superuser=True)
        user.set_password('admin')
        user.put()
    return redirect('/account/login')
