from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomTokenObtainPairSerializer, CustomGroupSerializer,CustomUserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = CustomGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_queryset = super().get_queryset()
        return group_queryset.exclude(name='member')
    

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset= CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]


    @action(detail=False, methods=['post'], url_path='staff/create')
    def create_member():
        

        return Response()
    

    @action(detail=False, methods=['post'], url_path='member/create')
    def create_member():

        return Response()


