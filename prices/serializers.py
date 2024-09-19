from .models import Referral,Matching
from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin

from members.serializers import AccountSerializer

class ReferralSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    downline = AccountSerializer(many=False)

    class Meta:
        model = Referral
        fields = '__all__'


class MatchingSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Matching
        fields = '__all__'