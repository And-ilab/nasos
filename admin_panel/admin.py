from django.contrib import admin

from django.contrib import admin
from .models import User


# class UserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'email', 'role')
#     search_fields = ('email', 'first_name', 'second_name')
#
#
# admin.site.register(User, UserAdmin)