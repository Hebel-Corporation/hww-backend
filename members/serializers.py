from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin
from members.models import *


class CountrySerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class LocationSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    # country = CountrySerializer(many=False, read_only=True)

    class Meta:
        model = Location
        fields = '__all__'


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
    class Meta:
        model = Account
        fields = '__all__'
        depth = 1

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


