from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, EmailTracker


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("email","name","is_verified","is_superuser", "is_staff", "is_active",)
    list_filter = ("email","name","is_verified","is_superuser", "is_staff", "is_active",)
    fieldsets = (
        (None, {"fields": ("email","name", "password")}),
        ("Permissions", {"fields": ("is_verified","is_superuser","is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email","name", "password1", "password2","is_verifed","is_superuser", "is_staff",
                "is_active", "groups", "user_permissions"
            )}
        ),
    )
    search_fields = ("email","name",)
    ordering = ("email","name",)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(EmailTracker)