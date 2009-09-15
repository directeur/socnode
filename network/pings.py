#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

import logging
import urllib
from google.appengine.api import urlfetch

def publish_ping(hub_url, feed_url):
    """
    spec: http://pubsubhubbub.googlecode.com/svn/trunk/pubsubhubbub-core-0.1.html
    Informs hub_url that feed_url has been updated
    """
    success = False
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    post_params = {
        'hub.mode': 'publish',
        'hub.url': feed_url,
    }
    payload = urllib.urlencode(post_params)
    try:
        response = urlfetch.fetch(hub_url, method='POST', payload=payload)
    except urlfetch.Error:
        logging.exception('Failed to deliver publishing message to %s', hub_url)
    else:
        logging.info('URL fetch status_code=%d, content="%s"',
                  response.status_code, response.content)
        if response.status_code == 200:
            success = True 
    return success


def subscribe_ping(hub_url, mode, callback, topic, verify='sync',
        verify_token='', lease_seconds=''):
    """
    spec: http://pubsubhubbub.googlecode.com/svn/trunk/pubsubhubbub-core-0.1.html
    verify € {'sync', 'async'}
    mode € {"subscribe" , "unsubscribe"}
    """
    success = False
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    post_params = {
        'hub.mode': mode,
        'hub.callback': callback,
        'hub.topic': topic,
        'hub.verify': verify,
        'hub.verify_token': verify_token,
        'hub.lease_seconds': lease_seconds,
    }
    payload = urllib.urlencode(post_params)
    try:
        response = urlfetch.fetch(hub_url, method='POST', payload=payload)
    except urlfetch.Error:
        logging.exception('Failed to deliver subscription message to %s', hub_url)
    else:
        logging.info('URL fetch status_code=%d, content="%s"',
                  response.status_code, response.content)
        if response.status_code == 200:
            success = True 
    return success
