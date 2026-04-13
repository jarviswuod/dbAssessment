from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Role

User = get_user_model()

admin.site.register(Role)
admin.site.register(User)
