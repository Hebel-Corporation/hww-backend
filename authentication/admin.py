from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,Staff,Member

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin,admin.ModelAdmin):
    # list_display = ['id', 'username', 'first_name', 'last_name', 'is_active', 'is_office_admin']
    list_display = ['id','is_admin', 'username', 'created_at']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user','is_office_admin', 'is_logistician', 'is_technician']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['user','company_id', 'full_name', 'phone']
