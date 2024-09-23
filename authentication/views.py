from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomTokenObtainPairSerializer, CustomGroupSerializer,CustomUserSerializer
from members.serializers import AccountSerializer
from app.pagination import CustomPagination


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = CustomGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_queryset = super().get_queryset()
        return group_queryset.exclude(name='membre')
    
    

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset= CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination


    @action(detail=False, methods=['get'], url_path='members')
    def members(self,request):
        member_queryset = CustomUser.objects.filter(user_type='member')

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(member_queryset, request)

        member_serializer = CustomUserSerializer(paginated_queryset, many=True, exclude=['username', 'password'])

        return paginator.get_paginated_response(member_serializer.data)
    


    @action(detail=True, methods=['get'], url_path='member-details')
    def member_details(self, request, pk):
        member_instance = self.get_object()
        member_serializer = CustomUserSerializer(member_instance, many=False, exclude=['username', 'password', 'office', 'groups'])

        return Response(data={
            **member_serializer.data,
            "accounts": AccountSerializer(member_instance.accounts.all(), many=True, exclude=['member', 'lft', 'rght', 'tree_id', 'level']).data
        }, status=status.HTTP_200_OK)


