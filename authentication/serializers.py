from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
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
    downline_count = serializers.SerializerMethodField()
    accounts_number = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'username', 
            'password', 
            'first_name', 
            'last_name', 
            'gender', 
            'birthday', 
            'downline_count', 
            'accounts_number', 
            'company_id', 
            'phone', 
            'user_type',
            'office',
            'groups',
            'has_default_password',
            'date_joined'
            ]
        extra_kwargs = {
            'password': {'write_only' : True},
        }

    
    def get_downline_count(self, instance):
        count = 0
        member_accounts = instance.accounts.all()
        for account in member_accounts :
            count += account.get_descendants(include_self=False).count()

        return count
    

    def get_accounts_number(self, instance):
        return instance.accounts.count()

    
    def __init__(self, *args, **kwargs):

        exclude_fields = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)

        if exclude_fields:
            for field in exclude_fields:
                self.fields.pop(field)



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, attrs):
        token = super().get_token(attrs)

        # Add custom claims
        token['user'] = CustomUserSerializer(attrs).data

        return token




class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True) #, validators=[validate_password]
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"message": "Les mots de passe ne correspondent pas."})
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError({"message": "l'ancien mot de passe est incorrect."})
        return value
