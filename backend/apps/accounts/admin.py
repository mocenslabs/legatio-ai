"""
Django Admin configuration for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User, UserProfile


class UserProfileInline(admin.StackedInline):  # type: ignore[type-arg]
    model = UserProfile
    can_delete = False
    verbose_name = "profile"
    verbose_name_plural = "profile"
    fk_name = "user"


@admin.register(User)
class UserAdmin(BaseUserAdmin):  # type: ignore[type-arg]
    inlines = (UserProfileInline,)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_verified",
        "two_factor_enabled",
        "date_joined",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_verified",
        "two_factor_enabled",
        "date_joined",
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Two-Factor Authentication", {"fields": ("two_factor_enabled",)}),
        ("Preferences", {"fields": ("preferred_language", "preferred_timezone")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "is_active",
                    "is_staff",
                    "is_verified",
                ),
            },
        ),
    )
    readonly_fields = ("date_joined", "last_login")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "display_name", "created_at", "updated_at")
    search_fields = ("user__email", "display_name")
    readonly_fields = ("created_at", "updated_at")
