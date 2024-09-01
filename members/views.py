from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from members.models import *
from .serializers import *
from authentication.serializers import CustomUserSerializer, CustomGroupSerializer
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

    def create(self, request):
        api_data = request.data
        country = get_object_or_404(Country, id=api_data.get('country'))
        location_serializer = LocationSerializer(data=api_data)
        location_serializer.is_valid(raise_exception=True)
        location_serializer.save(country=country)
        
        return Response(data=location_serializer.data, status=status.HTTP_200_OK)



class OfficeViewSet(viewsets.ModelViewSet) :
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='staffs')
    def staffs(self,request, pk=None):
        instance = self.get_object()
        staff_queryset = instance.offices_set.filter(user_type='staff')
        staff_serializer = CustomUserSerializer(staff_queryset, many=True)

        return Response(data=staff_serializer.data, status=status.HTTP_200_OK)


    def create(self, request):
        office_data = request.data.get('office')
        staff_data = request.data.get('staff')

        # Récupération de l'instance Location
        location_instance = get_object_or_404(Location, id=office_data.pop('location'))

        try:
            with transaction.atomic():
                # Sérialisation et validation des données du bureau
                office_serializer = OfficeSerializer(data=office_data)
                office_serializer.is_valid(raise_exception=True)
                
                # Création du bureau
                office = office_serializer.save(location=location_instance)
                office.office_code = "0393"
                office.save()

                if staff_data.get("user_type") != "staff":
                    raise UserNotStaffException()

                staff_groups = Group.objects.filter(id__in=staff_data.get("groups", []))
                if len(staff_groups) != len(staff_data.get("groups", [])):
                    raise UserInvalidGroupException()

                # Sérialisation et validation des données du staff
                staff_serializer = CustomUserSerializer(data=staff_data)
                staff_serializer.is_valid(raise_exception=True)

                # Création de l'utilisateur staff
                staff = staff_serializer.save(company_id='00973')
                staff.groups.set(staff_groups)
                staff.office = office
                staff.save()

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "office": OfficeSerializer(office).data,
            "staff": CustomUserSerializer(staff).data
        }, status=status.HTTP_201_CREATED)

    
    
    
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