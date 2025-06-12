from django.contrib import admin
from .models import *


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'downline', 'amount', 'office', 'is_paid', 'created_at']




@admin.register(Matching)
class MatchingAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'display_downlines', 'amount', 'office', 'is_paid', 'created_at']
    filter_horizontal = ('downlines',)


    def display_downlines(self, obj):
        return " --&&-- ".join(tag.member.company_id for tag in obj.downlines.all())
    display_downlines.short_description = 'Downlines'




@admin.register(PurchaseBonus)
class PurchaseBonusAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'amount', 'amount_to_be_paid', 'office', 'is_paid', 'created_at']




@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['account', 'office', 'amount', 'payment_type', 'created_at']

