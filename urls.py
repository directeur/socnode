# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from ragendja.auth.urls import urlpatterns as auth_patterns
from blog.forms import UserRegistrationForm
from django.contrib import admin

admin.autodiscover()

handler500 = 'ragendja.views.server_error'

urlpatterns = auth_patterns + patterns('',
    (r'^admin/', include(admin.site.urls)),
    # Override the default registration form
    url(r'^account/register/$', 'registration.views.register',
        kwargs={'form_class': UserRegistrationForm},
        name='registration_register'),

    (r'^subscriptions/', include('subscriptions.urls')),
    (r'', include('blog.urls')),
)
