from django.contrib import admin
from .models import *


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'downline', 'amount', 'is_paid', 'created_at']




@admin.register(Matching)
class MatchingAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'amount', 'is_paid', 'created_at']




@admin.register(PurchaseBonus)
class PurchaseBonusAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'amount', 'amount_to_be_paid', 'is_paid', 'created_at']




@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['account', 'office', 'amount', 'payment_type', 'created_at']

