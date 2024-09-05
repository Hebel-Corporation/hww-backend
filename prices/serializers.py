from .models import Referral
from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin


class ReferralSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = '__all__'