from rest_framework import serializers
from drf_queryfields import QueryFieldsMixin
from members.models import *


class OfficeSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'


class PackageSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'



class MemberSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Member
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
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return self.flatten_account(instance, representation)

    def flatten_account(self, instance, representation):
        children = instance.get_children()
        if children:
            representation['children'] = [self.flatten_account(child, {}) for child in children]
        return representation
    


class SubscriptionSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'


