from django.contrib import admin

from groupchat.models import *

# Register your models here.

admin.site.register(Group)
admin.site.register(Message)