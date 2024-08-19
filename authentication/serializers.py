from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from members.serializers import MemberSerializer

from .models import CustomUser
from members.models import Member


class CustomUserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    member = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['username', 'created_at','groups', 'member']
        extra_kwargs = {
            'id':{'read_only' : True},
            'created_at':{'read_only' : True},
            }

    def get_groups(self,user):
        user_groups = user.groups.all()
        return [group.name for group in user_groups]

    def get_member(self,user):
        if not user.is_admin:
            try:
                member = user.member
                return MemberSerializer(member).data
            except Member.DoesNotExist:
                return None
        return None
    
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        if args[0].is_admin:
            self.fields.pop('member')
        else:
            self.fields.pop('groups')
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['user_data'] = CustomUserSerializer(user).data

        return token