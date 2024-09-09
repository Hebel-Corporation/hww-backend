from django.contrib import admin
from .models import *

@admin.register(MatchingPrice)
class MatchingPriceAdmin(admin.ModelAdmin):
    list_display = ['id','begin', 'end', 'package_price_percent']
