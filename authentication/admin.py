from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin,admin.ModelAdmin):
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'first_name', 'last_name','user_type','company_id', 'office']
    # fieldsets = ['id', 'username', 'first_name', 'last_name', 'is_active', 'is_office_admin']
