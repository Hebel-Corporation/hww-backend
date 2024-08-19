from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Office, Package, Member, Account, Subscription


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'office_type', 'is_active', 'created_at']
    


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'description', 'created_at']



@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'company_id']



@admin.register(Account)
class AccountAdmin(MPTTModelAdmin):
    mptt_indent_field = "id"
    list_display = ['id', 'member', 'package', 'referral_account', 'parent', 'is_active', 'created_at']



@admin.register(Subscription)
class SubscriptionAdmin(MPTTModelAdmin):
    list_display = ['id', 'office', 'member_account', 'created_at']


