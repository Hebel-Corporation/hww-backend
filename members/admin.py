from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Office, Package, Account, Subscription, Country, Location


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'created_at']



@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'country','code', 'created_at']



@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'location', 'office_type','company_id', 'is_active', 'created_at']
    


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'description', 'created_at']




@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    mptt_indent_field = "id"
    list_display = ['id', 'member','company_id', 'package', 'referral_account', 'parent', 'is_active', 'created_at']



@admin.register(Subscription)
class SubscriptionAdmin(MPTTModelAdmin):
    list_display = ['id', 'office', 'member_account', 'created_at']


