from django.contrib import admin
from blog.models import Entry

class EntryAdmin(admin.ModelAdmin):
    list_display = ('author', 'author_url', 'body', 'link', 'published', 'updated')
    search_fields = ('author',)
    list_filter = ('published', 'updated')
    ordering = ('-updated',)
    fields = ('body', 'link')


admin.site.register(Entry, EntryAdmin)
