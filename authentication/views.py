from rest_framework import viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomTokenObtainPairSerializer, CustomGroupSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = CustomGroupSerializer
    # permission_classes = [IsAuthenticated]
