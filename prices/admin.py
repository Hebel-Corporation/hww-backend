from django.contrib import admin
from .models import *


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'downline', 'amount', 'office', 'is_paid', 'created_at']
    search_fields = ['grantee__company_id']
    list_filter = ['is_paid', 'created_at']



@admin.register(Matching)
class MatchingAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'display_downlines', 'amount', 'office', 'is_paid', 'created_at', 'is_validated']
    filter_horizontal = ('downlines',)
    search_fields = ['grantee__company_id']
    list_filter = ['is_paid', 'created_at']


    def display_downlines(self, obj):
        return " --&&-- ".join(tag.member.company_id for tag in obj.downlines.all())
    display_downlines.short_description = 'Downlines'


    




@admin.register(PurchaseBonus)
class PurchaseBonusAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'amount', 'amount_to_be_paid', 'office', 'is_paid', 'created_at']
    search_fields = ['grantee__company_id']
    list_filter = ['is_paid', 'created_at']



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['account', 'office', 'amount', 'payment_type', 'created_at']



@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'mark', 'image', 'created_at', 'updated_at']



@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['title', 'unit_number', 'unit_type', 'equivalent_amount', 'gift', 'is_active', 'created_at', 'member_count']

    def member_count(self, obj):
        return obj.get_reward_qualification_count
    member_count.short_description = 'Qualification Count'


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'is_active', 'member_count']

    def member_count(self, obj):
        return obj.get_account_qualification_count
    member_count.short_description = 'Qualification Count'



@admin.register(PromotionItem)
class PromotionItemAdmin(admin.ModelAdmin):
    list_display = ['promotion', 'equivalent_amount', 'unit_number', 'unit_type', 'gift', 'member_count']

    def member_count(self, obj):
        return obj.account_promotions.count()
    member_count.short_description = 'Qualification Count'




