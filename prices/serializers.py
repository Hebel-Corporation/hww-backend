from .models import Referral,Matching
from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin


class ReferralSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = '__all__'


class MatchingSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Matching
        fields = '__all__'