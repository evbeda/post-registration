from django.contrib import admin

from .models import FileDoc, FileType, Event

admin.site.register(FileDoc)
admin.site.register(FileType)
admin.site.register(Event)
