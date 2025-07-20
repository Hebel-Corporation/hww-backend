from .models import Referral, Matching, Payment, PurchaseBonus, Promotion, PromotionItem, Reward, Gift
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


class PurchaseBonusSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    sale_detail = SaleDetailSerializer(many=False)

    class Meta:
        model = PurchaseBonus
        fields = '__all__'



class PaymentSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    office = OfficeSerializer(many=False)

    class Meta:
        model = Payment
        fields = '__all__'


class GiftSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    
    class Meta:
        model = Gift
        fields = '__all__'


class PromotionSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    qualification_count = serializers.SerializerMethodField()
    total_bonus_concerned = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = '__all__'
        
    def get_qualification_count(self, obj):
        return obj.get_promotion_qualification_count

    def get_total_bonus_concerned(self, obj):

        count = 0

        if any(promoItem.unit_type == 'matching' for promoItem in obj.promotionitem_set.all()):
            count += Matching.objects.filter(
                created_at__range=(obj.start_date, obj.end_date)
            ).count()
        if any(promoItem.unit_type == 'referral' for promoItem in obj.promotionitem_set.all()):
            count += Referral.objects.filter(
                created_at__range=(obj.start_date, obj.end_date)
            ).count()
        
        return count

class PromotionItemSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    
    promotion = PromotionSerializer(many=False, read_only=True)
    gift = GiftSerializer(many=False, read_only=True)
    
    class Meta:
        model = PromotionItem
        fields = '__all__'


class RewardSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    
    gift = GiftSerializer(many=False, read_only=True)
    qualification_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Reward
        fields = '__all__'
        
    def get_qualification_count(self, obj):
        return obj.get_reward_qualification_count