from django.contrib import admin
from .models import *


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['id', 'grantee', 'downline', 'amount', 'created_at']



@admin.register(Matching)
class MatchingAdmin(admin.ModelAdmin):
    list_display = ['id', 'grantee', 'amount', 'created_at']

