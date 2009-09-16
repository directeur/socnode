from django.contrib import admin
from subscriptions.models import Subscription

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'feed_url', 'is_service', 'hub', 'updated')
    search_fields = ('title',)
    list_filter = ('updated',)
    ordering = ('-updated',)
    fields = ('title', 'url', 'feed_url')


admin.site.register(Subscription, SubscriptionAdmin)
