#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
from django.http import HttpResponse
from django.utils import simplejson

def json_response(data):
    json = simplejson.dumps(data)
    return HttpResponse('(%s)'%json, mimetype='text/javascript')

