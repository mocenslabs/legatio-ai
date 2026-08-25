"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_verified', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_verified', 'two_factor_enabled', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions',
         {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Security', {'fields': ('two_factor_enabled', 'totp_secret')}),
        ('Preferences', {'fields': ('preferred_language', 'preferred_timezone')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff',
                       'is_superuser'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""

    list_display = ('user', 'display_name', 'created_at', 'updated_at')
    search_fields = ('user__email', 'display_name')
    readonly_fields = ('created_at', 'updated_at')
