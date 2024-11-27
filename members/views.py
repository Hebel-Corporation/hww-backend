from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from members.models import *
from .serializers import *
from authentication.serializers import CustomUserSerializer, CustomGroupSerializer
from authentication.models import CustomUser
from django.contrib.auth.models import Group
from utils.custom_error_exceptions import UserNotStaffException, UserInvalidGroupException
from utils.utils_functions import create_account

from config.serializers import SubscriptionCodeSerializer
from config.models import SubscriptionCode
from prices.models import Referral, Matching, Payment, PurchaseBonus
from prices.serializers import ReferralSerializer, MatchingSerializer, PaymentSerializer
from prices.filters import MatchingFilter

from django.conf import settings


class CountryViewSet(viewsets.ModelViewSet) :
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]



class LocationViewSet(viewsets.ModelViewSet) :
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'country__name', 'country__code']

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
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'office_code', 'location__name']


    @action(detail=True, methods=['get'], url_path='staffs')
    def staffs(self,request, pk):
        instance = get_object_or_404(Office, id=pk)
        search_value = request.query_params.get('search', '')

        if search_value:
            staff_queryset = instance.offices_set.filter(
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value) |
                Q(company_id__icontains=search_value),
                user_type='staff'
            )
        else:
            staff_queryset = instance.offices_set.filter(user_type='staff')

        staff_serializer = CustomUserSerializer(staff_queryset, many=True, exclude=['username', 'password'])

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
        last_staff_instance = CustomUser.objects.filter(user_type='staff').order_by('-date_joined').first()
        staff_id = last_staff_instance.company_id.split('-').pop()
        staff = staff_serializer.save(company_id=f"{'-'.join(last_staff_instance.company_id.split('-')[:-1])}-{settings.STAFF_COMPANY_ID__INITIAL}{int(staff_id[1:])+1}")
        staff.groups.set(staff_groups)
        staff.set_password(staff_data.get('password'))
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

                member_id = f"{settings.COMPANY_INITIAL}-{office_instance.office_code}-{settings.MEMBER_COMPANY_ID_INITIAL}{CustomUser.objects.filter(user_type='member').count()+1}"
                member_data['username'] = ''.join(member_id.split('-'))
                member_data['password'] = settings.MEMBER_DEFAULT_PASSWORD
                member_serialiser = CustomUserSerializer(data=member_data)
                member_serialiser.is_valid(raise_exception=True)

                member = member_serialiser.save(company_id=member_id)
                member_group = Group.objects.get(name='membre')
                member.groups.set([member_group])
                member.set_password(settings.MEMBER_DEFAULT_PASSWORD)
                member.office = office_instance
                member.save()

                # all create account function
                account = create_account(
                    referral=referral_account, 
                    sponsor=sponsor_account, 
                    member=member, 
                    office=office_instance, 
                    package_id=package_id
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

                # all create account function
                account = create_account(
                    referral=referral_account, 
                    sponsor=sponsor_account, 
                    member=member, 
                    office=office_instance, 
                    package_id=package_id
                )
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data=AccountSerializer(account).data,status=status.HTTP_201_CREATED)
    



    @action(detail=True, methods=['get'], url_path='get-register-codes')
    def get_register_codes(self,request, pk=None):
        instance = self.get_object()
        code_queryset = instance.office_codes.all()
        code_serializer = SubscriptionCodeSerializer(code_queryset, many=True)

        return Response(data=code_serializer.data, status=status.HTTP_200_OK)



    @action(detail=True, methods=['get'], url_path='check-register-code-validity')
    def check_register_code_validity(self,request, pk=None):
        office_instance = self.get_object()
        has_valid_code = office_instance.office_codes.filter(is_valid=True).exists()
        
        return Response(data=has_valid_code, status=status.HTTP_200_OK)




    @action(detail=True, methods=['post'], url_path='generate-register-code')
    def generate_register_code(self,request, pk=None):

        office_instance = self.get_object()

        api_data = request.data
        package_id = api_data.get('package', None)

        try :
            with transaction.atomic():

                package = get_object_or_404(Package, id=package_id)

                subscription_code = SubscriptionCode.objects.create(
                    office=office_instance,
                    package=package,
                    reccords_number=api_data.get('codeNumber', 0),
                    amount_paid=api_data.get('amount', 0)
                )
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data=SubscriptionCodeSerializer(subscription_code).data,status=status.HTTP_201_CREATED)




    @action(detail=True, methods=['post'], url_path='register-member-payment')
    def register_member_payment(self,request, pk=None):

        office_instance = self.get_object()

        api_data = request.data

        try :
            with transaction.atomic():
                account_instance = get_object_or_404(Account, id=api_data.get('account', None))
                bonuse_ids = api_data.get('bonuses', [])
                payment_type = api_data.get('payment_type')

                if payment_type == 'matching_payment' :
                    Matching.objects.filter(id__in=bonuse_ids).update(is_paid=True)
                elif payment_type == 'referral_payment' :
                    Referral.objects.filter(id__in=bonuse_ids).update(is_paid=True)
                elif payment_type == 'purchase_payment' :
                    PurchaseBonus.objects.filter(id__in=bonuse_ids).update(is_paid=True)
                else :
                    raise ValidationError("Le type de payment est obligatoire !") 

                payment = Payment.objects.create(
                    office = office_instance,
                    account = account_instance,
                    amount = api_data.get('amount'),
                    payment_type = payment_type,
                    bonuses = bonuse_ids
                )
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data=PaymentSerializer(payment).data,status=status.HTTP_201_CREATED)
    


    def create(self, request):
        office_data = request.data.get('office')
        staff_data = request.data.get('staff')

        # Récupération de l'instance Location
        location_instance = get_object_or_404(Location, id=office_data.pop('location'))

        try:
            with transaction.atomic():
                
                # Création du bureau
                office = Office.objects.create(
                    name=office_data.get('name', ''),
                    location=location_instance,
                    office_code= f'{location_instance.name[:3].upper()}0{Office.objects.filter(location=location_instance).count()+1}'
                )

                if staff_data.get("user_type") != "staff":
                    raise UserNotStaffException()

                staff_groups = Group.objects.filter(id__in=staff_data.get("groups", []))
                if len(staff_groups) != len(staff_data.get("groups", [])):
                    raise UserInvalidGroupException()

                # Sérialisation et validation des données du staff
                staff_serializer = CustomUserSerializer(data=staff_data)
                staff_serializer.is_valid(raise_exception=True)

                # Création de l'utilisateur staff
                staff_count = CustomUser.objects.filter(user_type="staff").count()
                staff = staff_serializer.save(company_id=f"{settings.COMPANY_INITIAL}-{office.office_code}-{settings.STAFF_COMPANY_ID__INITIAL}{staff_count+1}")
                staff.groups.set(staff_groups)
                staff.set_password(staff_data.get('password'))
                staff.office = office
                staff.save()

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "office": OfficeSerializer(office).data,
            "staff": CustomUserSerializer(staff, exclude=['username', 'password']).data
        }, status=status.HTTP_201_CREATED)

    




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

                if not sponsor_account in referral_account.get_descendants(include_self=True) :
                    return Response(data={
                        "is_valid" : False,
                        "error_type": "sponsor_id",
                        "message": "Ce sponsor n'est pas dans le même réseau que le parrain spécifier."
                    }, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
                
                # if sponsor_account.get_descendant_count() >= 2 :
                if sponsor_account.get_children().count() >= 2 :
                    return Response(data={
                        "is_valid" : False,
                        "error_type": "sponsor_id",
                        "message": "Ce sponsor a déjà atteinds le nombre maximal des enfants direct."
                    }, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
                else :
                    return Response(data={
                        "is_valid": True
                    }, status=status.HTTP_200_OK)

            except Account.DoesNotExist :
                return Response(data={
                    "is_valid" : False,
                    "error_type": "sponsor_id",
                    "message": "Ce sponsor n'existe pas dans aucun réseau de la plateforme."
                }, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            
        except Account.DoesNotExist :
            return Response(data={
                    "is_valid" : False,
                    "error_type": "parrain_id",
                    "message": "Ce parrain n'existe pas dans la plateforme."
                }, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)



    @action(detail=True, methods=['get'], url_path='member-downlines')
    def member_downlines(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')

        paginator = self.pagination_class()
        downline_queryset = account_instance.get_descendants(include_self=False).order_by('created_at')

        if search_value:
            downline_queryset = downline_queryset.filter(
                Q(member__first_name__icontains=search_value) |
                Q(member__last_name__icontains=search_value) |
                Q(member__company_id__icontains=search_value) |
                Q(company_id__icontains=search_value) 
            )

        paginated_queryset = paginator.paginate_queryset(downline_queryset, request)
        account_serializer = AccountSerializer(paginated_queryset, many=True, exclude=['balance', 'rewards', 'matching_count', 'referral_count', 'lft', 'rght', 'tree_id', 'level', 'office'])

        return paginator.get_paginated_response(account_serializer.data)



    @action(detail=True, methods=['get'], url_path='account-details')
    def account_details(self, request, pk):
        account_instance = self.get_object()
        account_serializer = AccountSerializer(account_instance, many=False, exclude=['lft', 'rght', 'tree_id', 'level'])

        return Response(data=account_serializer.data, status=status.HTTP_200_OK)
    


    @action(detail=True, methods=['get'], url_path='member-referrals')
    def member_referrals(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')

        if search_value:
            referral_queryset = Referral.objects.filter(
                Q(downline__member__first_name__icontains=search_value) |
                Q(downline__member__last_name__icontains=search_value) |
                Q(downline__member__company_id__icontains=search_value) |
                Q(downline__company_id__icontains=search_value),
                grantee=account_instance 
            )
        else:
            referral_queryset = Referral.objects.filter(grantee=account_instance)

        # Appliquer le filtre Django Filter
        filter_instance = MatchingFilter(request.GET, queryset=referral_queryset)
        filtered_queryset = filter_instance.qs  # Récupère les résultats filtrés

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
        referral_serializer = ReferralSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(referral_serializer.data)
    



    @action(detail=True, methods=['get'], url_path='member-matchings')
    def member_matchings(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')
        # search_value = request.query_params.get('search', '')

        if search_value:
            matching_queryset = Matching.objects.filter(
                Q(downlines__member__first_name__icontains=search_value) |
                Q(downlines__member__last_name__icontains=search_value) |
                Q(downlines__member__company_id__icontains=search_value) |
                Q(downlines__company_id__icontains=search_value),
                grantee=account_instance 
            ).distinct()
        else:
            matching_queryset = Matching.objects.filter(grantee=account_instance)


        # Appliquer le filtre Django Filter
        filter_instance = MatchingFilter(request.GET, queryset=matching_queryset)
        filtered_queryset = filter_instance.qs  # Récupère les résultats filtrés

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
        matching_serializer = MatchingSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(matching_serializer.data)
    




    @action(detail=True, methods=['get'], url_path='member-payments')
    def member_payments(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')

        if search_value:
            payment_queryset = Payment.objects.filter(
                Q(payment_type__icontains=search_value),
                account=account_instance 
            ).distinct()
        else:
            payment_queryset = Payment.objects.filter(account=account_instance)

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(payment_queryset, request)
        payment_serializer = PaymentSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(payment_serializer.data)




    @action(detail=True, methods=['get'], url_path='account-network')
    def account_network(self, request, pk):
        account_instance = self.get_object()
        referral_serializer = AccountSerializer(account_instance.referral_account, many=False, exclude=['lft', 'rght', 'tree_id', 'level'])
        sponsor_serializer = AccountSerializer(account_instance.parent, many=False, exclude=['lft', 'rght', 'tree_id', 'level'])
        dowlines_serializer = AccountSerializer(account_instance.get_children(), many=True, exclude=['lft', 'rght', 'tree_id', 'level'])

        return Response(data={
            'referral': referral_serializer.data,
            'sponsor': sponsor_serializer.data,
            'children': dowlines_serializer.data
        }, status=status.HTTP_200_OK)



class SubscriptionViewSet(viewsets.ModelViewSet) :
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]