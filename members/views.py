from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from members.models import *
from .serializers import *
from authentication.serializers import CustomUserSerializer
from authentication.models import CustomUser
from django.contrib.auth.models import Group
from utils.custom_error_exceptions import UserNotStaffException, UserInvalidGroupException


class CountryViewSet(viewsets.ModelViewSet) :
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]



class LocationViewSet(viewsets.ModelViewSet) :
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]



class OfficeViewSet(viewsets.ModelViewSet) :
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
    
        office_data = request.data.get('office')
        staff_data = request.data.get('staff')

        location_instance = get_object_or_404(Location, id=office_data['location'])
        s = OfficeSerializer(data=location_instance)
        print("location_instance+++++++++++++", location_instance)
        office_data['office_code'] = "KIN-0033"
        office_data['location'] = s.data
        office_serializer = OfficeSerializer(data=office_data)
        if not office_serializer.is_valid():
            raise ValidationError(office_serializer.errors)

        staff_data['company_id'] = 'Mdr-093'
        staff_serializer = CustomUserSerializer(data=staff_data)
        if not staff_serializer.is_valid():
            raise ValidationError(staff_serializer.errors)
        
        if not staff_data.get("user_type")=="staff":
            raise UserNotStaffException()
        
        staff_groups = Group.objects.filter(id__in=staff_data.get("groups"))
        if len(staff_groups) != len(staff_data.get("groups")):
            raise UserInvalidGroupException()
        
        staff_data.pop("groups")


        office = office_serializer.save()

        staff = CustomUser.objects.create_user(**staff_data)
        staff.groups.set(staff_groups)
        staff.office=office
        staff.save

        return Response({"office":office_serializer.data,"staff":CustomUserSerializer(staff).data},
                         status=status.HTTP_201_CREATED)
    
    
    
    @action(detail=False, methods=['post'], url_path='assign_staff')
    def assign_staff():

        return Response()



class PackageViewSet(viewsets.ModelViewSet) :
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]



class AccountViewSet(viewsets.ModelViewSet) :
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]



class SubscriptionViewSet(viewsets.ModelViewSet) :
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]