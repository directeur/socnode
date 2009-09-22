#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
import logging
from django.http import HttpResponse
from django.utils import simplejson
from django.core.cache import cache

def json_response(data):
    json = simplejson.dumps(data)
    return HttpResponse('(%s)'%json, mimetype='text/javascript')

def keygen(format, *args, **kwargs):
    """generates a key from args and kwargs using format"""
    allargs = args+tuple(kwargs[key] for key in sorted(kwargs.keys()))
    key = format % allargs[0:format.count('%')]
    return key

# cache decorator
def memoize(keyformat, time=0, cache_null=False):
    """Decorator to memoize functions using django cache."""
    def decorator(fxn):
        def wrapper(self, *args, **kwargs):
            key = keygen(keyformat, *args, **kwargs)
            data = cache.get(key)
            if data is not None:
                logging.info('From memcache: %s' % key)
                return data
            logging.info('Computed value: %s' % key)
            data = fxn(self, *args, **kwargs)
            if data or cache_null:
                cache.set(key, data, time)
            return data
        wrapper.__doc__ = fxn.__doc__
        wrapper.__dict__ = fxn.__dict__
        return wrapper
    return decorator

def remember(key, value, time=0):
    cache.set(key, value, time)

def forget(key):
    cache.delete(key)
