from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from .models import CustomUser,Member,Staff

from django.contrib.auth import get_user_model


User = get_user_model()

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['is_office_admin', 'is_logistician', 'is_technician']


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['company_id', 'full_name', 'phone']


class CustomUserSerializer(serializers.ModelSerializer):
    staff = serializers.SerializerMethodField()
    member = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['username', 'created_at','staff', 'member']
        extra_kwargs = {
            'id':{'read_only' : True},
            'created_at':{'read_only' : True},
            }

    def get_staff(self,obj):
        if obj.is_admin:
            try:
                staff = Staff.objects.get(user=obj)
                return StaffSerializer(staff).data
            except Staff.DoesNotExist:
                return None
        return None

    def get_member(self,obj):
        if not obj.is_admin:
            try:
                member = Member.objects.get(user=obj)
                return MemberSerializer(member).data
            except Member.DoesNotExist:
                return None
        return None
    
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        print(self.fields)
        if args[0].is_admin:
            self.fields.pop('member')
        else:
            self.fields.pop('staff')
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['user_data'] = CustomUserSerializer(user).data

        return token