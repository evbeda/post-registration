from django.contrib import admin
from .models import Doc, FileType, Event

admin.site.register(Doc)
admin.site.register(FileType)
admin.site.register(Event)
