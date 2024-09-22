from .models import Referral,Matching
from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin

from members.serializers import AccountSerializer

class ReferralSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    downline = AccountSerializer(many=False, exclude=['balance', 'rewards', 'matching_count', 'referral_count', 'lft', 'rght', 'tree_id', 'level', 'office'])

    class Meta:
        model = Referral
        fields = '__all__'


class MatchingSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    downlines = AccountSerializer(many=True, exclude=['balance', 'rewards', 'matching_count', 'referral_count', 'lft', 'rght', 'tree_id', 'level', 'office'])

    class Meta:
        model = Matching
        fields = '__all__'