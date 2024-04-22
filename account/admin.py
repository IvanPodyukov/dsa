from django.contrib import admin

from account.models import Interest, User


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ['email', 'full_name', 'description']
