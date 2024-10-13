from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CustomTokenObtainPairSerializer, 
    CustomGroupSerializer,
    CustomUserSerializer,
    ChangePasswordSerializer
    )
from members.serializers import AccountSerializer
from app.pagination import CustomPagination
from django.db.models import Q


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


     # This is the custom action for changing the password
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request, pk=None):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            if user.has_default_password :
                user.has_default_password = False
            user.save()
            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    @action(detail=False, methods=['get'], url_path='members')
    def members(self,request):
        search_value = request.query_params.get('search', '')

        if search_value:
            member_queryset = CustomUser.objects.filter(
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value) |
                Q(company_id__icontains=search_value),
                user_type='member'
            )
        else:
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


