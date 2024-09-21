from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password', 'last_login')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'gender', 'birthday', 'email', 'phone', 'office')}),
        ('Permissions', {'fields': ('groups', 'user_type', 'is_active', 'is_staff', 'is_superuser')}),
        (None, {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'company_id', 'email', 'user_type', 'first_name', 'last_name', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('date_joined',)
