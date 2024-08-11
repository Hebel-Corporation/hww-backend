from django.contrib import admin
from .models import CustomUser



@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'first_name', 'last_name', 'is_active', 'is_office_admin']
    # fieldsets = ['id', 'username', 'first_name', 'last_name', 'is_active', 'is_office_admin']
