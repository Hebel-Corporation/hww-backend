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
        member_data = api_data.get('member')
        uplines_data = api_data.get('uplines')
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


    def get_account_by_company_id(self, request):

        company_id = request.query_params.get('company_id', None)

        if company_id is None:
            return Response({'error': 'ID de la compangie requis.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Account.objects.get(company_id=company_id)
        except Account.DoesNotExist:
            return Response({'error': 'Le compte associé a l\'ID renseigné n\'a pas été trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        
        return instance
    

    @action(detail=False, methods=['get'])
    def get_by_company_id(self,request):
        
        instance = self.get_account_by_company_id(request=request)

        if type(instance) is Response:
            return instance

        return Response({"account_id":instance.id},status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['get'])
    def sponsor_is_valid(self,request):
        
        referral_id = request.query_params.get('referral_id', None)

        instance = self.get_account_by_company_id(request=request)
        if type(instance) is Response:
            return instance
        

        sponsor_account = instance

        if(sponsor_account.get_children().count()>1):
            return Response({'error': 'Le sponsor a déjà deux downlines.'}, status=status.HTTP_400_BAD_REQUEST)
        

        referral_account = Account.objects.get(id=referral_id)
        if not referral_account.get_descendants(include_self=True).filter(id=sponsor_account.id).exists():
           return Response({'error': 'Le sponsor et le parrain sont dans des réseaux differents.'}, status=status.HTTP_400_BAD_REQUEST) 

        return Response({"sponsor_account_id":sponsor_account.id},status=status.HTTP_200_OK)
    

    @action(detail=False,methods=['post'])
    def create_member(self,request):

        member_data = request.data.get('member')
        sponsor_account_id = request.data.get('sponsor_account')
        referral_account_id = request.data.get('referral_account')
        package_id = request.data.get('package')

        member_serialiser = CustomUserSerializer(data=member_data)
        if not member_serialiser.is_valid():
            return Response(member_serialiser.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # member = CustomUser.objects.create_user(**member_data)
        office = request.user.office
        # member.office = office
        # member.save()


        sponsor_account = Account.objects.get(id=sponsor_account_id)
        referral_account = Account.objects.get(id=referral_account_id)
        package = Package.objects.get(id=package_id)

        # account = Account.objects.create(
        #     member=member,
        #     # company_id = "",
        #     package = package,
        #     referral_account = referral_account,
        #     parent = sponsor_account,

        # )

        # return Response({"data":AccountSerializer(account).data},status=status.HTTP_201_CREATED)
        return Response()
    
    @action(detail=False,methods=["get"])
    def test(self,request):

        import re
        from enum import Enum

        class IdType(Enum):
            OFFICE = 1
            STAFF = 2
            MEMBER = 3
            ACCOUNT = 4

        def get_new_company_id(id_type:IdType,office=None,member=None):

            last_instance = None
            new_company_id =''

            if(id_type==IdType.ACCOUNT):
                last_instance = Account.objects.filter(member=member).order_by('-created_at').first()
            else:
                last_instance = CustomUser.objects.filter(user_type="staff" if id_type==IdType.STAFF else "member").order_by('-date_joined').first()
            
            user_initial = "S" if id_type==IdType.STAFF else "M"  

            if last_instance:
            
                last_instance_id = int(re.findall(r'[0-9]+',last_instance.company_id.split('-').pop()).pop())
                
                if id_type==IdType.ACCOUNT:
                    new_company_id = member.company_id+"-"+str(last_instance_id+1).zfill(2)
                else:
                    new_company_id = office.company_id+"-"+user_initial+str(last_instance_id+1).zfill(5)
            else:

                if id_type==IdType.ACCOUNT:
                    new_company_id = member.company_id+"-"+"1".zfill(2)
                else:
                    new_company_id = office.company_id+"-"+user_initial+"1".zfill(5)

            return new_company_id


        member = CustomUser.objects.filter(user_type="member").first()
        print("=======>",get_new_company_id(IdType.ACCOUNT,member=member))

        return Response()
    @action(detail=False, methods=['post'], url_path='check-uplines-validity')
    def check_uplines_validity(self,request):
        api_data = request.data

        try :
            referral_account = Account.objects.get(company_id=api_data.get('referral_account', None))

            try :
                sponsor_account = Account.objects.get(company_id=api_data.get('sponsor_account', None))

                if not referral_account in sponsor_account.get_descendants(include_self=True) :
                    return Response(data={
                        "is_valid" : False,
                        "error_type": "sponsor_id",
                        "message": "Ce sponsor n'est pas dans le même réseau que le parrain spécifier."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if sponsor_account.get_descendant_count() >= 2 :
                    return Response(data={
                        "is_valid" : False,
                        "error_type": "sponsor_id",
                        "message": "Ce sponsor a déjà atteinds le nombre maximal des enfants direct."
                    }, status=status.HTTP_400_BAD_REQUEST)
                else :
                    return Response(data={
                        "is_valid": True
                    }, status=status.HTTP_200_OK)

            except Account.DoesNotExist :
                return Response(data={
                    "is_valid" : False,
                    "error_type": "sponsor_id",
                    "message": "Ce sponsor n'existe pas dans aucun réseau de la plateforme."
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Account.DoesNotExist :
            return Response(data={
                    "is_valid" : False,
                    "error_type": "parrain_id",
                    "message": "Ce parrain n'existe pas dans la plateforme."
                }, status=status.HTTP_400_BAD_REQUEST)



class SubscriptionViewSet(viewsets.ModelViewSet) :
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]