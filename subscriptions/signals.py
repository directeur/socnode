#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
from django.dispatch import Signal

#signal sent after some publishing
post_subscribe = Signal(providing_args=['host', 'instance', 'created'])
pre_unsubscribe = Signal(providing_args=['host', 'instance'])
