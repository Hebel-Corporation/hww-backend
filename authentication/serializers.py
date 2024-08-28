from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import Group

from .models import CustomUser



class CustomGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ['id', 'name']



class CustomUserSerializer(serializers.ModelSerializer):

    groups = CustomGroupSerializer(many=True,required=False,read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'first_name','last_name', 'company_id', 'phone', 'user_type','office','groups']
        extra_kwargs = {
            'id': {'read_only' : True},
            'password': {'write_only' : True},
            'company_id': {'read_only' : True},
            'created_at': {'read_only' : True},
        }



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, attrs):
        token = super().get_token(attrs)
        
        # Add custom claims
        # user_data = CustomUserSerializer(attrs).data
        # print("======>",user_data)
        # token['user'] = user_data 

        return token