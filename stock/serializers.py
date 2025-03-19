from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin

from .models import SaleDetail


class SaleDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    class Meta:
        model = SaleDetail
        fields = '__all__'
        depth = 3
