from django.contrib import admin
from django.contrib.auth.models import Group, User

from .models import TgUser, Cart

admin.site.unregister(Group)
admin.site.unregister(User)

admin.site.register(TgUser)
admin.site.register(Cart)
