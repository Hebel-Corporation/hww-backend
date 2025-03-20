from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin
from members.models import *
from authentication.models import CustomUser


class CountrySerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class LocationSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    country = CountrySerializer(many=False, read_only=True)
    offices_count = serializers.SerializerMethodField()
    subscription_rate = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = '__all__'
    

    def get_offices_count(self, instance):
        return instance.offices.count()
    

    def get_subscription_rate(self, instance):
        offices = instance.offices.all()
        count = 0
        for office in offices :
            count += office.subscriptions.count()

        subscriptions_count = Subscription.objects.count()
        
        try :
            percentage = (count * 100) / subscriptions_count
            return round(percentage, 2)
        except :
            return 0


class OfficeSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    location = LocationSerializer(many=False, read_only=True)
    members_count = serializers.SerializerMethodField()
    subscription_rate = serializers.SerializerMethodField()

    class Meta:
        model = Office
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only' : True},
            'is_active':{'read_only':True},
            'created_at': {'read_only' : True},
        }



    def get_members_count(self, instance):
        return instance.subscriptions.count()
    

    def get_subscription_rate(self, instance):
        members_count = instance.subscriptions.count()
        subscriptions_count = Subscription.objects.count()
        
        try :
            percentage = (members_count * 100) / subscriptions_count
            return round(percentage, 2)
        except :
            return 0



class PackageSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    class Meta:
        model = Package
        fields = '__all__'



class AccountSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    balance = serializers.SerializerMethodField()
    # pvs = serializers.SerializerMethodField()
    downline_count = serializers.SerializerMethodField()
    matching_count = serializers.SerializerMethodField()
    referral_count = serializers.SerializerMethodField()
    # puchase_bonus_count = serializers.SerializerMethodField()
    member = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = '__all__'



    def __init__(self, *args, **kwargs):

        exclude_fields = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)

        if exclude_fields:
            for field in exclude_fields:
                self.fields.pop(field)



    def get_balance(self, instance):
        return instance.get_balance
    
    # def get_pvs(self, instance):
    #     return instance.get_pvs
    

    def get_matching_count(self, instance):
        return instance.get_matching_count


    def get_referral_count(self, instance):
        return instance.get_referral_count
    

    # def get_puchase_bonus_count(self, instance):
    #     return instance.get_puchase_bonus_count



    def get_downline_count(self, instance):
        return instance.get_descendants(include_self=False).count()



    def get_member(self, instance):
        return {
            "id": instance.member.id,
            "first_name": instance.member.first_name,
            "last_name": instance.member.last_name,
            "gender": instance.member.gender,
            "company_id": instance.member.company_id,
            "phone": instance.member.phone,
            "user_type": instance.member.user_type,
        }


    # children = serializers.SerializerMethodField()

    # def get_children(self, obj):
    #     return AccountSerializer(obj.get_children(), many=True).data

    
    # Other solution to render flat object list
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         return self.flatten_account(instance, representation)

#     def flatten_account(self, instance, representation):
#         children = instance.get_children()
#         if children:
#             representation['children'] = [self.flatten_account(child, {}) for child in children]
#         return representation
    


class SubscriptionSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'


