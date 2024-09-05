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



    @action(detail=True, methods=['post'], url_path='create-staff')
    def create_staff(self,request, pk=None):
        office_instance = self.get_object()

        staff_data = request.data
        
        if staff_data.get("user_type") != "staff":
            raise UserNotStaffException()

        staff_groups = Group.objects.filter(id__in=staff_data.get("groups", []))
        if len(staff_groups) != len(staff_data.get("groups", [])):
            raise UserInvalidGroupException()

        # Sérialisation et validation des données du staff
        staff_serializer = CustomUserSerializer(data=staff_data)
        staff_serializer.is_valid(raise_exception=True)

        # Création de l'utilisateur staff
        staff = staff_serializer.save(company_id='009S973')
        staff.groups.set(staff_groups)
        staff.office = office_instance
        staff.save()

        return Response(data=staff_serializer.data, status=status.HTTP_201_CREATED)



    
    @action(detail=True, methods=['post'], url_path='member-registration')
    def create_member(self,request, pk=None):

        office_instance = self.get_object()

        api_data = request.data
        member_data = api_data.get('member', None)
        uplines_data = api_data.get('uplines', None)
        package_id = api_data.get('package', None)

        try :
            with transaction.atomic():

                is_first_node = Account.objects.count() < 1

                referral_account = None if is_first_node else get_object_or_404(Account, company_id=uplines_data.get('referral_account', None))
                sponsor_account = None if is_first_node else get_object_or_404(Account, company_id=uplines_data.get('sponsor_account', None))

                member_serialiser = CustomUserSerializer(data=member_data)
                member_serialiser.is_valid(raise_exception=True)

                member = member_serialiser.save()
                member_group = Group.objects.get(name='member')
                member.groups.set(member_group)
                member.office = office_instance
                member.save()

                package = None
                if package_id :
                    package = get_object_or_404(Package, id=package_id)
                else :
                    package = Package.objects.filter(is_default=True).first()

                account = Account.objects.create(
                    member=member,
                    office = office_instance,
                    company_id = "009M973",
                    package = package,
                    referral_account = referral_account,
                    sponsor_account = sponsor_account,
                )
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data=member_serialiser.data,status=status.HTTP_201_CREATED)
    


    @action(detail=True, methods=['post'], url_path='member-registration-account')
    def create_member_account(self,request, pk=None):

        office_instance = self.get_object()

        api_data = request.data
        package_id = api_data.get('package', None)

        try :
            with transaction.atomic():

                referral_account = get_object_or_404(Account, company_id=api_data.get('referral_account', None))
                sponsor_account = get_object_or_404(Account, company_id=api_data.get('sponsor_account', None))
                member = get_object_or_404(CustomUser, id=api_data.get('member', None))

                package = None
                if package_id :
                    package = get_object_or_404(Package, id=package_id)
                else :
                    package = Package.objects.filter(is_default=True).first()

                account = Account.objects.create(
                    member=member,
                    office = office_instance,
                    company_id = "009M973",
                    package = package,
                    referral_account = referral_account,
                    sponsor_account = sponsor_account,
                )
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data=AccountSerializer(account).data,status=status.HTTP_201_CREATED)
    


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


    @action(detail=False, methods=['get'], url_path='is-first-node')
    def is_first_node(self,request, pk=None):

        return Response(data={
            "is_first_node": Account.objects.count() < 1
        }, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='check-uplines-validity')
    def check_uplines_validity(self,request):
        api_data = request.data

        if Account.objects.count() < 1 :
            return Response(data={
                    "is_valid": True
                }, status=status.HTTP_200_OK)

        try :
            referral_account = Account.objects.get(company_id=api_data.get('referral_account', None))

            try :
                sponsor_account = Account.objects.get(company_id=api_data.get('sponsor_account', None))

                if not referral_account in sponsor_account.get_descendants(include_self=True) :
                    return Response(data={
                        "is_valid" : False,
                        "error_type": "sponsor_id",
                        "message": "Ce sponsor n'est pas dans le même réseau que le parrain spécifier."
                    }, status=status.HTTP_202_ACCEPTED)
                
                if sponsor_account.get_descendant_count() >= 2 :
                    return Response(data={
                        "is_valid" : False,
                        "error_type": "sponsor_id",
                        "message": "Ce sponsor a déjà atteinds le nombre maximal des enfants direct."
                    }, status=status.HTTP_202_ACCEPTED)
                else :
                    return Response(data={
                        "is_valid": True
                    }, status=status.HTTP_200_OK)

            except Account.DoesNotExist :
                return Response(data={
                    "is_valid" : False,
                    "error_type": "sponsor_id",
                    "message": "Ce sponsor n'existe pas dans aucun réseau de la plateforme."
                }, status=status.HTTP_202_ACCEPTED)
            
        except Account.DoesNotExist :
            return Response(data={
                    "is_valid" : False,
                    "error_type": "parrain_id",
                    "message": "Ce parrain n'existe pas dans la plateforme."
                }, status=status.HTTP_202_ACCEPTED)



class SubscriptionViewSet(viewsets.ModelViewSet) :
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]