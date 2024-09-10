from django.contrib import admin
from .models import *


@admin.register(SubscriptionCode)
class SubscriptionCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'reccords_number', 'equivalent_amount', 'office', 'package', 'is_valid', 'created_at', 'updated_at']



@admin.register(MatchingPrice)
class MatchingPriceAdmin(admin.ModelAdmin):
    list_display = ['id','begin', 'end', 'package_price_percent']


    