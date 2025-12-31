from sre_constants import POSSESSIVE_REPEAT_ONE
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Min
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
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
from utils.utils_functions import create_account, get_period_filtered_bonus_queryset

from config.serializers import SubscriptionCodeSerializer
from config.models import SubscriptionCode
from prices.models import Referral, Matching, Payment, PurchaseBonus, Promotion, PromotionItem, Reward
from prices.serializers import ReferralSerializer, MatchingSerializer, PaymentSerializer, PurchaseBonusSerializer, PromotionSerializer, PromotionItemSerializer, RewardSerializer
from prices.filters import MatchingFilter, ReferralFilter, PurchaseBonusFilter
from stock.models import SaleDetail
from stock.serializers import SaleDetailSerializer

from django.conf import settings
from django.db.models.functions import TruncMonth
from datetime import datetime, date
import calendar
import json
from django.utils import timezone
from datetime import timedelta
from itertools import chain


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


    @action(detail=True, methods=['get'], url_path='statistics')
    def statistics(self,request, pk):
        office_instance = get_object_or_404(Office, id=pk)
        search_value = request.query_params.get('search', '')
        office_id = request.query_params.get('office_id', None)

        valid_matchings_queryset = []
        blacklisted_matchings_queryset = []
        accounts_queryset = []
        purchase_bonus_queryset = []
        
        # Récupérer tous les comptes qualifiés pour les récompenses
        reward_ids = Reward.objects.values_list('id', flat=True)
        reward_qualifications = Account.objects.filter(rewards__in=reward_ids)

        promotion_item_ids = PromotionItem.objects.values_list('id', flat=True)
        promotion_qualifications = Account.objects.filter(promotions__in=promotion_item_ids)

        if office_instance.office_type == 'head_office':
            valid_matchings_queryset = Matching.objects.filter(is_validated=True) if office_id is None or office_id == 'all' else Matching.objects.filter(office__id=office_id, is_validated=True)
            blacklisted_matchings_queryset = Matching.objects.filter(is_validated=False) if office_id is None or office_id == 'all' else Matching.objects.filter(office__id=office_id, is_validated=False)
            accounts_queryset = Account.objects.all() if office_id is None or office_id == 'all' else Account.objects.filter(office__id=office_id)
            purchase_bonus_queryset = PurchaseBonus.objects.all() if office_id is None or office_id == 'all' else PurchaseBonus.objects.filter(office__id=office_id)
            reward_qualifications = reward_qualifications if office_id is None or office_id == 'all' else reward_qualifications.filter(office__id=office_id)
            promotion_qualifications = promotion_qualifications if office_id is None or office_id == 'all' else promotion_qualifications.filter(office__id=office_id)
            
        elif office_instance.office_type == 'sub_office' :
            valid_matchings_queryset = Matching.objects.filter(office=office_instance, is_validated=True)
            blacklisted_matchings_queryset = Matching.objects.filter(office=office_instance, is_validated=False)
            accounts_queryset = Account.objects.filter(office=office_instance)
            purchase_bonus_queryset = PurchaseBonus.objects.filter(office=office_instance)
            reward_qualifications = reward_qualifications.filter(office=office_instance)
            promotion_qualifications = promotion_qualifications.filter(office=office_instance)

        current_year = datetime.now().year

        subscriptions = (
            accounts_queryset
            .filter(created_at__year=current_year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        purchase_bonus = (
            purchase_bonus_queryset
            .filter(created_at__year=current_year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        valid_matchings = (
            valid_matchings_queryset
            .filter(created_at__year=current_year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )
        blacklisted_matchings = (
            blacklisted_matchings_queryset
            .filter(created_at__year=current_year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        # Créer une liste de 12 mois avec 0 par défaut
        accounts_result = []
        purchase_bonus_result = []
        valid_matchings_result = []
        blacklisted_matchings_result = []
        month_map = {sub["month"].month: sub["total"] for sub in subscriptions}
        purchase_bonus_month_map = {sub["month"].month: sub["total"] for sub in purchase_bonus}
        valid_matchings_month_map = {sub["month"].month: sub["total"] for sub in valid_matchings}
        blacklisted_matchings_month_map = {sub["month"].month: sub["total"] for sub in blacklisted_matchings}

        for m in range(1, 13):
            accounts_result.append({
                "month": calendar.month_name[m],
                "value": month_map.get(m, 0)
            })
            purchase_bonus_result.append({
                "month": calendar.month_name[m],
                "value": purchase_bonus_month_map.get(m, 0)
            })
            valid_matchings_result.append({
                "month": calendar.month_name[m],
                "value": valid_matchings_month_map.get(m, 0)
            })
            blacklisted_matchings_result.append({
                "month": calendar.month_name[m],
                "value": blacklisted_matchings_month_map.get(m, 0)
            })


        stat_data = {
            "accounts": accounts_queryset.count(),
            "valid_matchings": valid_matchings_queryset.count(),
            "blacklisted_matchings": blacklisted_matchings_queryset.count(),
            "purchase_bonus": purchase_bonus_queryset.count(),
            "rewards": reward_qualifications.count() + promotion_qualifications.count(),
            "stat_data": [
                {
                    "label": "Enregistrements",
                    "data": accounts_result
                },
                {
                    "label": "Bonus achat produits",
                    "data": purchase_bonus_result
                },
                {
                    "label": "Equilibres valides",
                    "data": valid_matchings_result
                },
                {
                    "label": "Equilibres bloqués",
                    "data": blacklisted_matchings_result
                }
            ]
        }

        return Response(data=stat_data, status=status.HTTP_200_OK)



    @action(detail=True, methods=['get'], url_path='activities')
    def activities(self, request, pk):
        office_instance = self.get_object()
        period_filter = request.query_params.get('filter', '')
        activity_type = request.query_params.get('activity_type', '')
        office_id = request.query_params.get('office_filter', None)

        now = timezone.now()

        if period_filter == 'all' :
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False, is_validated=True).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False).order_by('-created_at')
            payments = Payment.objects.all().order_by('-created_at')
        elif period_filter == 'daily' :
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False, created_at__date=now.date()).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False, created_at__date=now.date(), is_validated=True).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False, created_at__date=now.date()).order_by('-created_at')
            payments = Payment.objects.filter(created_at__date=now.date()).order_by('-created_at')
        elif period_filter == 'weekly' :
            start_of_week = now - timedelta(days=now.weekday())  # Lundi
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False, created_at__date__gte=start_of_week.date()).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False, created_at__date__gte=start_of_week.date(), is_validated=True).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False, created_at__date__gte=start_of_week.date()).order_by('-created_at')
            payments = Payment.objects.filter(created_at__date__gte=start_of_week.date()).order_by('-created_at')
        elif period_filter == 'monthly' :
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False, created_at__year=now.year, created_at__month=now.month).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False, created_at__year=now.year, created_at__month=now.month, is_validated=True).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False, created_at__year=now.year, created_at__month=now.month).order_by('-created_at')
            payments = Payment.objects.filter(created_at__year=now.year, created_at__month=now.month).order_by('-created_at')


        
        if office_id and office_id != 'all' and office_instance.office_type == 'head_office' :
            purchase_bonus = purchase_bonus.filter(office__id=office_id)
            matchings = matchings.filter(office__id=office_id)
            referrals = referrals.filter(office__id=office_id)
            payments = payments.filter(account__office__id=office_id)
        elif office_instance.office_type == 'sub_office':
            purchase_bonus = purchase_bonus.filter(office=office_instance)
            matchings = matchings.filter(office=office_instance)
            referrals = referrals.filter(office=office_instance)
            payments = payments.filter(account__office=office_instance)
        
        if activity_type == 'PAYMENTS':
            payments_serialized = PaymentSerializer(payments, many=True)
            paginator = self.pagination_class()
            paginator.page_size = 15
            try:
                paginated_payments = paginator.paginate_queryset(payments_serialized.data, request)
            except Exception:
                # Forcer la page à 1 si la page demandée n'existe pas
                request.GET._mutable = True  # Permet de modifier les paramètres GET
                request.GET['page'] = '1'
                request.GET._mutable = False
                paginated_payments = paginator.paginate_queryset(payments_serialized.data, request)
            
            return paginator.get_paginated_response(paginated_payments)

        
        if activity_type == 'TOTALS':

            referral_ids = referrals.values_list('downline', flat=True)
            purchase_bonus_ids = purchase_bonus.values_list('sale_detail__member_account', flat=True)
            recent_matching_ids = [
                mt.downlines.order_by('-created_at').first().id
                for mt in matchings.prefetch_related('downlines')
                if mt.downlines.exists()
            ]

            all_bonus_ids = list(set(chain(referral_ids, purchase_bonus_ids, recent_matching_ids)))

            subscriptions = Subscription.objects.filter(
                member_account__in=all_bonus_ids
            ).distinct()

            if office_id and office_id != 'all' and office_instance.office_type == 'head_office' :
                subscriptions = subscriptions.filter(office__id=office_id)
            elif office_instance.office_type == 'sub_office':
                subscriptions = subscriptions.filter(office=office_instance)

            if period_filter == 'all' :
                pass
            elif period_filter == 'daily' :
                subscriptions = subscriptions.filter(created_at__date=now.date())
            elif period_filter == 'weekly' :
                start_of_week = now - timedelta(days=now.weekday()) 
                subscriptions = subscriptions.filter(created_at__date__gte=start_of_week.date())
            elif period_filter == 'monthly' :
                subscriptions = subscriptions.filter(created_at__year=now.year, created_at__month=now.month)

            total_matchings = matchings.aggregate(total=Sum('amount'))['total'] if matchings else 0
            total_referrals = referrals.aggregate(total=Sum('amount'))['total'] if referrals else 0
            total_purchase_bonus = purchase_bonus.aggregate(total=Sum('amount_to_be_paid'))['total'] if purchase_bonus else 0

            total_received = (subscriptions.aggregate(total=Sum('package__price'))['total'] or 0) + (purchase_bonus.aggregate(total=Sum('sale_detail__amount'))['total'] if purchase_bonus else 0)
            total_bonuses = total_matchings + total_referrals + total_purchase_bonus


            activity_data = {
                "purchase_bonus": total_purchase_bonus,
                "matchings": total_matchings,
                "referrals": total_referrals,
                "total_payment": payments.aggregate(total=Sum('amount'))['total'] or 0,
                "balance": {
                    "total_received": total_received,
                    "sold": total_received - total_bonuses
                }
            }

            return Response(data=activity_data, status=status.HTTP_200_OK)

        
        purchase_bonus_by_user = (
            purchase_bonus
            .values('grantee_id', 'grantee__id', 'grantee__company_id', 'grantee__member__first_name', 'grantee__member__last_name', 'office__office_code', 'office__name', 'office__location__name')
            .annotate(count=Count('id'), total_bonus=Sum('amount_to_be_paid'))
            .order_by('grantee_id')
        )


        matchings_by_user = (
            matchings
            .values('grantee_id', 'grantee__id', 'grantee__company_id', 'grantee__member__first_name', 'grantee__member__last_name', 'office__office_code', 'office__name', 'office__location__name')
            .annotate(count=Count('id'), total_bonus=Sum('amount'))
            .order_by('grantee_id')
        )
        

        referrals_by_user = (
            referrals
            .values('grantee_id', 'grantee__id', 'grantee__company_id', 'grantee__member__first_name', 'grantee__member__last_name', 'office__office_code', 'office__name', 'office__location__name')
            .annotate(count=Count('id'), total_bonus=Sum('amount'))
            .order_by('grantee_id')
        )


        bonuses = [
            {**record, 'bonus_type': 'Achat produit'+('s' if record['count'] > 1 else ''), 'bonus_type_code':'purchase_bonus'}
            for record in purchase_bonus_by_user
        ] + [
            {**record, 'bonus_type': 'Equilibre'+('s' if record['count'] > 1 else ''), 'bonus_type_code':'matching_bonus'}
            for record in matchings_by_user
        ] + [
            {**record, 'bonus_type': 'Parrainage'+('s' if record['count'] > 1 else ''), 'bonus_type_code':'referral_bonus'}
            for record in referrals_by_user
        ]


        paginator = self.pagination_class()
        paginator.page_size = 15

        sorted_bonuses = sorted(bonuses, key=lambda x: x.get('grantee__id', 0), reverse=True)
        try:
            paginated_bonuses = paginator.paginate_queryset(sorted_bonuses, request)
        except NotFound:
            # Forcer la page à 1 si la page demandée n'existe pas
            request.GET._mutable = True  # Permet de modifier les paramètres GET
            request.GET['page'] = '1'
            request.GET._mutable = False
            paginated_bonuses = paginator.paginate_queryset(sorted_bonuses, request)
        
        # paginated_bonuses = paginator.paginate_queryset(sorted(bonuses, key=lambda x: x.get('grantee__id', 0), reverse=True), request)


        return paginator.get_paginated_response(paginated_bonuses)



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
        from rapidfuzz import fuzz

        office_instance = self.get_object()

        api_data = request.data
        member_data = api_data.get('member', None)
        uplines_data = api_data.get('uplines', None)
        package_id = api_data.get('package', None)

        try :
            with transaction.atomic():
                if member_data:
                    first_name = member_data.get('first_name', '').strip()
                    last_name = member_data.get('last_name', '').strip()
                    current_full_name = f"{first_name} {last_name}".strip().lower()
                    
                    last_member = CustomUser.objects.all().order_by('-date_joined').first()

                    if last_member:
                        last_full_name = f"{last_member.first_name} {last_member.last_name}".strip().lower()
                        similarity_ratio = fuzz.ratio(current_full_name, last_full_name)
                        
                        # Si similarité > 95% et critères multiples correspondent
                        if similarity_ratio > 95 and last_member.office == office_instance and member_data.get('phone') == last_member.phone and member_data.get('gender') == last_member.gender:
                            # Retourner le membre existant
                            return Response(
                                {
                                    "error": "Un Membre avec des informations similaires a été créé récemment - Veuillez vérifier le réseau du membre pour en être sûr avant de créer un nouveau membre",
                                    "similarity": similarity_ratio,
                                    "details": "Un membre avec des informations similaires a été créé récemment"
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )

                is_first_node = Account.objects.count() < 1

                referral_account = None if is_first_node else get_object_or_404(Account, company_id=uplines_data.get('referral_account', None))
                sponsor_account = None if is_first_node else get_object_or_404(Account, company_id=uplines_data.get('sponsor_account', None))
                
                step = 0
                member_id = ""
                username = ""
                while True :
                    step += 1
                    member_id = f"{settings.COMPANY_INITIAL}-{office_instance.office_code}-{settings.MEMBER_COMPANY_ID_INITIAL}{CustomUser.objects.filter(user_type='member').count()+step}"
                    username = ''.join(member_id.split('-'))
                    if not CustomUser.objects.filter(username=username).exists():
                        break

                member_data['username'] = username
                member_data['password'] = settings.MEMBER_DEFAULT_PASSWORD
                member_serialiser = CustomUserSerializer(data=member_data)
                member_serialiser.is_valid(raise_exception=True)

                member = member_serialiser.save(company_id=member_id)
                member_group = Group.objects.get(name='membre')
                member.groups.set([member_group])
                member.set_password(settings.MEMBER_DEFAULT_PASSWORD)
                member.office = office_instance
                member.save()

                # call create account util function
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
        from datetime import timedelta

        office_instance = self.get_object()

        api_data = request.data
        package_id = api_data.get('package', None)
        member_id = api_data.get('member', None)

        try :
            with transaction.atomic():
                # Vérifier si un compte similaire a été créé récemment pour ce membre
                recent_time = timezone.now() - timedelta(minutes=2)
                recent_account = Account.objects.filter(
                    member__id=member_id,
                    office=office_instance,
                    created_at__gte=recent_time
                ).order_by('-created_at').first()
                
                if recent_account:
                    
                    if (recent_account.referral_account.company_id == api_data.get('referral_account', None) and 
                        recent_account.parent.company_id == api_data.get('sponsor_account', None)):
                        return Response(
                            {
                                "message": "Le compte similaire a été créé récemment - Veuillez vérifier le réseau du membre pour en être sûr avant de créer un nouveau compte",
                                "data": AccountSerializer(recent_account).data
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                referral_account = get_object_or_404(Account, company_id=api_data.get('referral_account', None))
                sponsor_account = get_object_or_404(Account, company_id=api_data.get('sponsor_account', None))
                member = get_object_or_404(CustomUser, id=member_id)

                # call create account util function
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
    


    @action(detail=True, methods=['post'], url_path='member-registration-purchase')
    def create_member_purchase(self,request, pk=None):

        office_instance = self.get_object()

        api_data = request.data
        account_id = api_data.get('accountID', None)
        amount = api_data.get('amount', 0)

        try :
            with transaction.atomic():

                account = get_object_or_404(Account, company_id=account_id)

                sale_detail = SaleDetail.objects.create(
                    member_account = account,
                    amount = amount,
                    office = office_instance,
                )
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data=SaleDetailSerializer(sale_detail).data,status=status.HTTP_201_CREATED)
    



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
                    if Matching.objects.filter(id__in=bonuse_ids, is_paid=False, is_validated=True).exists():
                        Matching.objects.filter(id__in=bonuse_ids, is_validated=True).update(is_paid=True)
                elif payment_type == 'referral_payment' :
                    if Referral.objects.filter(id__in=bonuse_ids, is_paid=False).exists():
                        Referral.objects.filter(id__in=bonuse_ids).update(is_paid=True)
                elif payment_type == 'purchase_payment' :
                    if PurchaseBonus.objects.filter(id__in=bonuse_ids, is_paid=False).exists():
                        PurchaseBonus.objects.filter(id__in=bonuse_ids).update(is_paid=True)
                else :
                    raise ValidationError("Le type de payment est obligatoire !") 

                payment, _ = Payment.objects.get_or_create(
                    office = office_instance,
                    account = account_instance,
                    amount = api_data.get('amount'),
                    payment_type = payment_type,
                    bonuses = bonuse_ids
                )
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data=PaymentSerializer(payment, exclude=['account']).data,status=status.HTTP_201_CREATED)
    


    @action(detail=True, methods=['post'], url_path='process-purchase-bonus-payment')
    def process_purchase_bonus_payment(self, request, pk=None):
        """
        Traite le paiement des bonus d'achat selon un algorithme spécifique :
        1. Cherche un bonus exactement égal au montant
        2. Cherche une combinaison de bonus égale au montant
        3. Réduit un bonus supérieur au montant
        """
        # from itertools import combinations
        
        office_instance = self.get_object()
        api_data = request.data
        budget = api_data.get('amount')
        account_instance = get_object_or_404(Account, id=api_data.get('account'))
        if 2 == 4:
            raise ValidationError("Cet compte n'a pas encore payé la maintenance")

        if not budget or budget <= 0:
            raise ValidationError("Le montant du paiement est invalide")

        try:

            with transaction.atomic():
                # Récupérer tous les bonus d'achat non payés
                bonuses = PurchaseBonus.objects.filter(
                    grantee=account_instance,
                    is_paid=False
                ).order_by('amount_to_be_paid')

                if not bonuses.exists():
                    raise ValidationError("Aucun bonus d'achat disponible")

                # Étape 1: Recherche de bonus exact
                exact_bonus = bonuses.filter(amount_to_be_paid=budget).first()
                if exact_bonus:
                    exact_bonus.is_paid = True
                    exact_bonus.amount_to_be_paid = 0
                    exact_bonus.save()
                    return create_payment_record(office_instance, account_instance, budget, [exact_bonus])

                #  if not combination_found:
                # 2. Chercher un bonus supérieur
                bonus_sup = bonuses.filter(amount_to_be_paid__gt=budget).first()
                if bonus_sup:
                    bonus_sup.amount_to_be_paid -= budget
                    bonus_sup.save()
                    return create_payment_record(office_instance, account_instance, budget, [bonus_sup])


                # Étape 3: Recherche de combinaisons avec somme légèrement supérieure
                paid_bonuses = []
                remaining_budget = budget

                # Trier les bonus par ordre croissant pour optimiser le traitement
                sorted_bonuses = sorted(bonuses, key=lambda x: x.amount_to_be_paid)

                for bonus in sorted_bonuses:
                    if bonus.amount_to_be_paid <= remaining_budget:
                        # Bonus entièrement utilisable
                        paid_bonuses.append(bonus)
                        remaining_budget -= bonus.amount_to_be_paid
                        bonus.is_paid = True
                        bonus.amount_to_be_paid = 0
                        bonus.save()

                        if remaining_budget == 0:
                            break
                    else:
                        # Bonus partiellement payé
                        bonus.amount_to_be_paid -= remaining_budget
                        bonus.save()
                        paid_bonuses.append(bonus)
                        break

                if not paid_bonuses:
                    raise ValidationError("Aucun bonus d'achat produit disponible pour ce montant")

                return create_payment_record(office_instance, account_instance, budget, paid_bonuses)

        except Exception as e:
            raise ValidationError(str(e))



    @action(detail=True, methods=['get'], url_path='promotions')
    def promotions(self, request, pk):
        office_instance = self.get_object()
        office_id = request.query_params.get('office_filter', None)
        search_value = request.query_params.get('search', '')
        prom_id = request.query_params.get('prom_id', None)

        promotion_serializer = None

        if not prom_id:
            promotions = Promotion.objects.all()
            promotion_serializer = PromotionSerializer(promotions, many=True, context={'request': request})
            promotion_serializer = promotion_serializer.data
        else:
            promotion = get_object_or_404(Promotion, id=prom_id)
            promotion_serializer = PromotionSerializer(promotion, many=False, context={'request': request}).data
        
            promotion_items = PromotionItem.objects.filter(promotion=promotion)
            member_accounts = Account.objects.filter(promotions__in=promotion_items)
            
            if office_id and office_id != 'all' and office_instance.office_type == 'head_office':
                member_accounts = member_accounts.filter(office__id=office_id)
            elif office_instance.office_type == 'sub_office':
                member_accounts = member_accounts.filter(office=office_instance)
                
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(member_accounts, request)
            
            serialized_accounts = AccountSerializer(paginated_queryset, many=True, context={'promotion': promotion}).data
            paginated_response = paginator.get_paginated_response(serialized_accounts)
            promotion_serializer['members'] = paginated_response.data
            
        return Response(promotion_serializer)
        


    @action(detail=True, methods=['get'], url_path='rewards')
    def rewards(self, request, pk):
        office_instance = self.get_object()
        office_id = request.query_params.get('office_filter', None)
        search_value = request.query_params.get('search', '')
        reward_id = request.query_params.get('reward_id', None)

        reward_serializer = None

        if not reward_id:
            rewards = Reward.objects.all().order_by('unit_number')
            reward_serializer = RewardSerializer(rewards, many=True, context={'request': request})
            reward_serializer = reward_serializer.data
        else:
            reward = get_object_or_404(Reward, id=reward_id)
            reward_serializer = RewardSerializer(reward, many=False, context={'request': request}).data
        
            member_accounts = Account.objects.filter(rewards=reward)
            
            if office_id and office_id != 'all' and office_instance.office_type == 'head_office':
                member_accounts = member_accounts.filter(office__id=office_id)
            elif office_instance.office_type == 'sub_office':
                member_accounts = member_accounts.filter(office=office_instance)
                
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(member_accounts, request)
            
            serialized_accounts = AccountSerializer(paginated_queryset, many=True).data
            paginated_response = paginator.get_paginated_response(serialized_accounts)
            reward_serializer['members'] = paginated_response.data
            
        return Response(reward_serializer)



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

    

def create_payment_record(office, account, amount, bonuses):
    payment = Payment.objects.create(
        office=office,
        account=account,
        amount=amount,
        payment_type='purchase_payment',
        bonuses=[str(bonus.id) for bonus in bonuses]
    )

    return Response({
        "message": f"Bonus d'achat traités pour {amount}$",
        "payment": PaymentSerializer(payment, exclude=['account']).data
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
        downline_queryset = account_instance.get_descendants(include_self=False).order_by('-created_at')

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


    

    @action(detail=True, methods=['get'], url_path='sponsor-accounts')
    def sponsor_accounts(self, request, pk):
        account_instance = self.get_object()
        position = request.query_params.get('position', '')
        
        if not position or position not in ['left', 'right']:
            return Response(
                data={"error": "Position parameter is required and must be 'left' or 'right'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        direct_children = account_instance.get_children().order_by('created_at')
        
        target_account = None
        
        if direct_children.count() == 0:
            target_account = account_instance
        elif direct_children.count() == 1:
            if position == 'left':
                target_account = direct_children.first()
            else:  
                target_account = account_instance
        else:
            if position == 'left':
                target_account = direct_children.first()
            else: 
                target_account = direct_children[1] if direct_children.count() > 1 else account_instance
        
        if (target_account == account_instance and 
            position == 'right' and 
            direct_children.count() == 1):
            network_accounts = [account_instance]
        else:
            network_accounts = list(target_account.get_descendants(include_self=True).order_by('created_at'))
            
            if (target_account != account_instance and 
                direct_children.count() == 1):
                network_accounts.append(account_instance)
        
        downline_data = [
            {
                "id": account.id,
                "full_name": f"{account.member.first_name} {account.member.last_name}",
                "company_id": account.company_id,
                "descendant_count": account.get_descendants(include_self=False).count()
            }
            for account in network_accounts
            if account.get_children().count() < 2
        ]

        return Response(data=downline_data, status=status.HTTP_200_OK)



    @action(detail=True, methods=['get'], url_path='account-details')
    def account_details(self, request, pk):
        account_instance = self.get_object()
        account_serializer = AccountSerializer(account_instance, many=False, exclude=['lft', 'rght', 'tree_id', 'level'])

        return Response(data=account_serializer.data, status=status.HTTP_200_OK)
    


    @action(detail=True, methods=['get'], url_path='member-referrals')
    def member_referrals(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')
        period_filter = request.query_params.get('period_filter', '')
        office_code = request.query_params.get('office_code', '')

        referral_queryset = Referral.objects.filter(grantee=account_instance).order_by('is_paid')
        if office_code :
            referral_queryset = referral_queryset.filter(office__office_code=office_code)

        if search_value:
            referral_queryset = Referral.objects.filter(
                Q(downline__member__first_name__icontains=search_value) |
                Q(downline__member__last_name__icontains=search_value) |
                Q(downline__member__company_id__icontains=search_value) |
                Q(downline__company_id__icontains=search_value)
            )

        
        if period_filter :
            referral_queryset = get_period_filtered_bonus_queryset(referral_queryset, period_filter)

        # Appliquer le filtre Django Filter
        filter_instance = ReferralFilter(request.GET, queryset=referral_queryset)
        filtered_queryset = filter_instance.qs  # Récupère les résultats filtrés

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
        referral_serializer = ReferralSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(referral_serializer.data)
    



    @action(detail=True, methods=['get'], url_path='member-matchings')
    def member_matchings(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')
        period_filter = request.query_params.get('period_filter', '')
        office_code = request.query_params.get('office_code', '')

        matching_queryset = Matching.objects.filter(grantee=account_instance, is_validated=True).order_by('is_paid')
        if office_code :
            matching_queryset = matching_queryset.filter(office__office_code=office_code)

        if search_value:
            matching_queryset = matching_queryset.filter(
                Q(downlines__member__first_name__icontains=search_value) |
                Q(downlines__member__last_name__icontains=search_value) |
                Q(downlines__member__company_id__icontains=search_value) |
                Q(downlines__company_id__icontains=search_value)
            ).distinct()


        if period_filter :
            matching_queryset = get_period_filtered_bonus_queryset(matching_queryset, period_filter)


        # Appliquer le filtre Django Filter
        filter_instance = MatchingFilter(request.GET, queryset=matching_queryset)
        filtered_queryset = filter_instance.qs  # Récupère les résultats filtrés

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
        matching_serializer = MatchingSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(matching_serializer.data)




    @action(detail=True, methods=['get'], url_path='member-purchases')
    def member_purchases(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')
        period_filter = request.query_params.get('period_filter', '')
        office_code = request.query_params.get('office_code', '')

        purchase_bonus_queryset = PurchaseBonus.objects.filter(grantee=account_instance).order_by('is_paid')
        if office_code :
            purchase_bonus_queryset = purchase_bonus_queryset.filter(office__office_code=office_code)

        if search_value:
            purchase_bonus_queryset = purchase_bonus_queryset.filter(
                Q(sale_detail__member_account__first_name__icontains=search_value) |
                Q(sale_detail__member_account__last_name__icontains=search_value) |
                Q(sale_detail__member_account__company_id__icontains=search_value)
            )

        if period_filter :
            purchase_bonus_queryset = get_period_filtered_bonus_queryset(purchase_bonus_queryset, period_filter)

        # Appliquer le filtre Django Filter
        filter_instance = PurchaseBonusFilter(request.GET, queryset=purchase_bonus_queryset)
        filtered_queryset = filter_instance.qs  # Récupère les résultats filtrés

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
        purchase_bonus_serializer = PurchaseBonusSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(purchase_bonus_serializer.data)
    




    @action(detail=True, methods=['get'], url_path='member-payments')
    def member_payments(self, request, pk):
        account_instance = self.get_object()
        search_value = request.query_params.get('search', '')

        payment_queryset = Payment.objects.filter(account=account_instance).order_by('-created_at')

        if search_value:
            payment_queryset = payment_queryset.filter(
                Q(payment_type__icontains=search_value)
            )

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(payment_queryset, request)
        payment_serializer = PaymentSerializer(paginated_queryset, many=True, exclude=['account'])

        return paginator.get_paginated_response(payment_serializer.data)




    @action(detail=True, methods=['get'], url_path='account-network')
    def account_network(self, request, pk):
        account_instance = self.get_object()
        referral_serializer = AccountSerializer(account_instance.referral_account, many=False, exclude=['lft', 'rght', 'tree_id', 'level'])
        sponsor_serializer = AccountSerializer(account_instance.parent, many=False, exclude=['lft', 'rght', 'tree_id', 'level'])
        dowlines_serializer = AccountSerializer(account_instance.get_children(), many=True, exclude=['lft', 'rght', 'tree_id', 'level'])

        # Calculer les PVs des enfants gauche et droite
        left_children = account_instance.get_children().filter(position='left')
        right_children = account_instance.get_children().filter(position='right')
        
        left_pvs = left_children.first().get_pvs if left_children.exists() else 0
        right_pvs = right_children.first().get_pvs if right_children.exists() else 0
        
        return Response(data={
            'referral': referral_serializer.data,
            'sponsor': sponsor_serializer.data,
            'children': dowlines_serializer.data,
            'pvs': {
                'left': left_pvs,
                'right': right_pvs,
                'stronger': 'left' if left_pvs > right_pvs else 'right' if left_pvs < right_pvs else 'equal'
            }
        }, status=status.HTTP_200_OK)
        




class SubscriptionViewSet(viewsets.ModelViewSet) :
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
