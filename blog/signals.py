#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
from django.dispatch import Signal

#signal sent after some publishing
post_publish = Signal(providing_args=['username', 'host'])
