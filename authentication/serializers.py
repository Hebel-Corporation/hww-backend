from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import Group

from .models import CustomUser



class CustomGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ['id', 'name']



class CustomUserSerializer(serializers.ModelSerializer):

    groups = CustomGroupSerializer(many=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name','last_name', 'email', 'company_id', 'phone', 'user_type', 'groups']
        extra_kwargs = {
            'id': {'read_only' : True},
            'created_at': {'read_only' : True},
        }



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, attrs):
        token = super().get_token(attrs)

        # Add custom claims
        token['user'] = CustomUserSerializer(attrs).data

        return token