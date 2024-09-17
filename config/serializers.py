from rest_framework import serializers
from .models import *

from members.serializers import PackageSerializer


class SubscriptionCodeSerializer(serializers.ModelSerializer) :

    total_amount = serializers.SerializerMethodField()
    package = PackageSerializer(many=False)

    class Meta:
        model=SubscriptionCode
        fields='__all__'
        

    
    def get_total_amount(self, instance) :
        return instance.total_amount