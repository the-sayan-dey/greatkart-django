from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile
from django.utils.html import format_html

# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'last_login','date_joined', 'is_active')
    list_display_links = ('email', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


'''

class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        return format_html('<img src="{}" width="30" style="border-radius: 50%;" >'.format(object.profile_picture.url))
    
    thumbnail.short_description = 'Profile  picture'
    list_display = ('thumbnail','user', 'city', 'state', 'country')


admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)


'''


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'user', 'city', 'state', 'country')

    def thumbnail(self, obj):
        # Safe way to access file URL — avoids ValueError when no file exists
        try:
            if obj.profile_picture and getattr(obj.profile_picture, 'name', None):
                return format_html(
                    '<img src="{}" width="30" style="border-radius:50%;" />',
                    obj.profile_picture.url
                )
        except ValueError:
            # In case the FileField raises ValueError internally
            pass

        # fallback: show dash or a small default placeholder image
        return format_html('<span style="color:#888;">-</span>')
    thumbnail.short_description = 'Profile picture'
    thumbnail.allow_tags = True

admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)