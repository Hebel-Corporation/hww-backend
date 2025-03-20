from .models import Referral, Matching, Payment#, PurchaseBonus
from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin

from members.serializers import AccountSerializer, OfficeSerializer
from stock.serializers import SaleDetailSerializer

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


# class PurchaseBonusSerializer(QueryFieldsMixin, serializers.ModelSerializer):

#     sale_detail = SaleDetailSerializer(many=False)

#     class Meta:
#         model = PurchaseBonus
#         fields = '__all__'



class PaymentSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    office = OfficeSerializer(many=False)

    class Meta:
        model = Payment
        fields = '__all__'