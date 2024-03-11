from django.contrib import admin

from account.models import Profile, Interest


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass
