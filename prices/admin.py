from django.contrib import admin
from .models import Referral,Matching


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['id', 'grantee', 'downline','amount','created_at']

@admin.register(Matching)
class MatchingAdmin(admin.ModelAdmin):
    list_display = ['id', 'grantee', 'get_downlines','amount','created_at']

    def get_downlines(self, obj):
        return " & ".join([account.company_id for account in obj.downlines.all()])
