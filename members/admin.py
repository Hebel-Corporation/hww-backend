from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Office, Package, Account, Subscription, Country, Location


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'created_at']



@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'country', 'created_at']



@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['id', 'office_code', 'name', 'location', 'office_type', 'is_active', 'created_at']
    


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'is_default', 'description', 'created_at', 'updated_at']




@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    mptt_indent_field = "id"
    list_display = ['member', 'company_id', 'referral_account', 'parent', 'office', 'is_active', 'created_at']
    search_fields = ['company_id', 'member__first_name', 'member__last_name']
    list_filter = ['is_active', 'office', 'created_at']

    actions = ['rebuild_mptt_tree']

    @admin.action(description="Reconstruire l’arbre MPTT")
    def rebuild_mptt_tree(self, request, queryset):
        for node in queryset:
            node._tree_manager.rebuild()
        self.message_user(request, "Arbre MPTT pour le modèle Account reconstruit avec succès ✅")



@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'office', 'package', 'member_account', 'created_at']


