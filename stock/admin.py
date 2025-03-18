from django.contrib import admin
from .models import *


@admin.register(SaleDetail)
class SaleDetailAdmin(admin.ModelAdmin):
    list_display = ['id', 'member_account', 'office', 'amount', 'created_at']
