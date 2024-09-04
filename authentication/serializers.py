from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import Group

from .models import CustomUser
from members.serializers import OfficeSerializer



class CustomGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ['id', 'name']



class CustomUserSerializer(serializers.ModelSerializer):
    office = OfficeSerializer(many=False, read_only=True)
    groups = CustomGroupSerializer(many=True,required=False, read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'first_name','last_name', 'gender', 'company_id', 'phone', 'user_type','office','groups']
        extra_kwargs = {
            'password': {'write_only' : True},
        }



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, attrs):
        token = super().get_token(attrs)
        
        # Add custom claims
        user_data = CustomUserSerializer(attrs).data
        # token['user'] = user_data 

        return token