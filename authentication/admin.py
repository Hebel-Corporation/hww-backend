from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin,admin.ModelAdmin):
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_id', 'username', 'user_type', 'first_name', 'last_name', 'is_active']
    # fieldsets = ['id', 'username', 'first_name', 'last_name', 'is_active', 'is_office_admin']
