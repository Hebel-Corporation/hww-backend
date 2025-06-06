from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Min
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
from utils.utils_functions import create_account, get_period_filtered_bonus_queryset

from config.serializers import SubscriptionCodeSerializer
from config.models import SubscriptionCode
from prices.models import Referral, Matching, Payment, PurchaseBonus
from prices.serializers import ReferralSerializer, MatchingSerializer, PaymentSerializer, PurchaseBonusSerializer
from prices.filters import MatchingFilter, ReferralFilter, PurchaseBonusFilter
from stock.models import SaleDetail
from stock.serializers import SaleDetailSerializer

from django.conf import settings
from django.db.models.functions import TruncMonth
from datetime import datetime
import calendar
import json
from django.utils import timezone
from datetime import timedelta


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

        matchings_queryset = []
        accounts_queryset = []
        purchase_bonus_queryset = []
        office_queryset = []

        if office_instance.office_type == 'head_office':
            matchings_queryset = Matching.objects.all() if office_id is None or office_id == 'all' else Matching.objects.filter(grantee__office__id=office_id)
            accounts_queryset = Account.objects.all() if office_id is None or office_id == 'all' else Account.objects.filter(office__id=office_id)
            purchase_bonus_queryset = PurchaseBonus.objects.all() if office_id is None or office_id == 'all' else PurchaseBonus.objects.filter(sale_detail__office__id=office_id)
            office_queryset = (
                Office.objects.all()
                    .values('id', 'office_code', 'location__name', 'name')
                )
        elif office_instance.office_type == 'sub_office' :
            matchings_queryset = Matching.objects.filter(grantee__office=office_instance)
            accounts_queryset = Account.objects.filter(office=office_instance)
            purchase_bonus_queryset = PurchaseBonus.objects.filter(sale_detail__office=office_instance)

        current_year = datetime.now().year

        subscriptions = (
            accounts_queryset
            .filter(created_at__year=current_year)
            .annotate(month=TruncMonth("created_at"))
            .values("month", 'office_id')
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

        matchings = (
            matchings_queryset
            .filter(created_at__year=current_year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        # Créer une liste de 12 mois avec 0 par défaut
        accounts_result = []
        purchase_bonus_result = []
        matchings_result = []
        month_map = {sub["month"].month: sub["total"] for sub in subscriptions}
        purchase_bonus_month_map = {sub["month"].month: sub["total"] for sub in purchase_bonus}
        matchings_month_map = {sub["month"].month: sub["total"] for sub in matchings}

        for m in range(1, 13):
            accounts_result.append({
                "month": calendar.month_name[m],
                "value": month_map.get(m, 0)
            })
            purchase_bonus_result.append({
                "month": calendar.month_name[m],
                "value": purchase_bonus_month_map.get(m, 0)
            })
            matchings_result.append({
                "month": calendar.month_name[m],
                "value": matchings_month_map.get(m, 0)
            })

        

       # Convertir les UUID en str
        if office_queryset is not None :
            office_list = [
                {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in item.items()}
                for item in office_queryset
            ]


        stat_data = {
            "accounts": accounts_queryset.count(),
            "matchings": matchings_queryset.count(),
            "purchase_bonus": purchase_bonus_queryset.count(),
            "rewards": 0,
            "offices": office_list,
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
                    "label": "Equilibres",
                    "data": matchings_result
                }
            ]
        }

        return Response(data=stat_data, status=status.HTTP_200_OK)



    @action(detail=True, methods=['get'], url_path='activities')
    def activities(self, request, pk):
        office_instance = self.get_object()
        period_filter = request.query_params.get('filter', '')
        activity_type = request.query_params.get('activity_type', '')

        now = timezone.now()

        if period_filter == 'all' :
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False).order_by('-created_at')
        elif period_filter == 'dayly' :
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False, created_at__date=now.date()).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False, created_at__date=now.date()).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False, created_at__date=now.date()).order_by('-created_at')
        elif period_filter == 'weekly' :
            start_of_week = now - timedelta(days=now.weekday())  # Lundi
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False, created_at__date__gte=start_of_week.date()).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False, created_at__date__gte=start_of_week.date()).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False, created_at__date__gte=start_of_week.date()).order_by('-created_at')
        elif period_filter == 'monthly' :
            purchase_bonus = PurchaseBonus.objects.filter(is_paid=False, created_at__year=now.year, created_at__month=now.month).order_by('-created_at')
            matchings = Matching.objects.filter(is_paid=False, created_at__year=now.year, created_at__month=now.month).order_by('-created_at')
            referrals = Referral.objects.filter(is_paid=False, created_at__year=now.year, created_at__month=now.month).order_by('-created_at')

        
        if activity_type == 'TOTALS':
            activity_data = {
                "purchase_bonus": purchase_bonus.aggregate(total=Sum('amount_to_be_paid'))['total'] or 0,
                "matchings": matchings.aggregate(total=Sum('amount'))['total'] or 0,
                "referrals": referrals.aggregate(total=Sum('amount'))['total'] or 0,
            }

            return Response(data=activity_data, status=status.HTTP_200_OK)

        
        purchase_bonus_by_user = (
            purchase_bonus
            .values('grantee_id', 'grantee__id', 'grantee__company_id', 'grantee__member__first_name', 'grantee__member__last_name', 'grantee__office__office_code', 'grantee__office__name', 'grantee__office__location__name')
            .annotate(count=Count('id'), total_bonus=Sum('amount_to_be_paid'))
            .order_by('grantee_id')
        )


        matchings_by_user = (
            matchings
            .values('grantee_id', 'grantee__id', 'grantee__company_id', 'grantee__member__first_name', 'grantee__member__last_name', 'grantee__office__office_code', 'grantee__office__name', 'grantee__office__location__name')
            .annotate(count=Count('id'), total_bonus=Sum('amount'))
            .order_by('grantee_id')
        )
        

        referrals_by_user = (
            referrals
            .values('grantee_id', 'grantee__id', 'grantee__company_id', 'grantee__member__first_name', 'grantee__member__last_name', 'grantee__office__office_code', 'grantee__office__name', 'grantee__office__location__name')
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

        print("================>>>>>>> #2 : ", len(bonuses))

        paginator = self.pagination_class()
        paginator.page_size = 30
        paginated_bonuses = paginator.paginate_queryset(sorted(bonuses, key=lambda x: x.get('grantee__id', 0), reverse=True), request)


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

        office_instance = self.get_object()

        api_data = request.data
        package_id = api_data.get('package', None)

        try :
            with transaction.atomic():

                referral_account = get_object_or_404(Account, company_id=api_data.get('referral_account', None))
                sponsor_account = get_object_or_404(Account, company_id=api_data.get('sponsor_account', None))
                member = get_object_or_404(CustomUser, id=api_data.get('member', None))

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
                    if Matching.objects.filter(id__in=bonuse_ids, is_paid=False).exists():
                        Matching.objects.filter(id__in=bonuse_ids).update(is_paid=True)
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
        
        return Response(data=PaymentSerializer(payment).data,status=status.HTTP_201_CREATED)
    


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
            # with transaction.atomic():
            #     # Récupérer tous les bonus d'achat non payés
            #     bonuses = PurchaseBonus.objects.filter(
            #         grantee=account_instance,
            #         is_paid=False
            #     ).order_by('amount_to_be_paid')

            #     if not bonuses.exists():
            #         return Response(
            #             {"error": "Aucun bonus d'achat disponible"}, 
            #             status=status.HTTP_400_BAD_REQUEST
            #         )

            #     # 1. Chercher un bonus exact
            #     exact_bonus = bonuses.filter(amount_to_be_paid=budget).first()
            #     if exact_bonus:
            #         exact_bonus.is_paid = True
            #         exact_bonus.amount_to_be_paid = 0
            #         exact_bonus.save()
            #         paid_bonuses = [str(exact_bonus.id)]
            #         message = f"Bonus d'achat payé avec montant exact de {budget}$"
                
            #     else:
            #         # 2. Chercher une combinaison
            #         combination_found = False
            #         paid_bonuses = []
                    
            #         for r in range(2, len(bonuses) + 1):
            #             for combo in combinations(bonuses, r):
            #                 if sum(b.amount_to_be_paid for b in combo) == budget:
            #                     for bonus in combo:
            #                         bonus.is_paid = True
            #                         bonus.amount_to_be_paid = 0
            #                         bonus.save()
            #                         paid_bonuses.append(str(bonus.id))
            #                     combination_found = True
            #                     message = f"Combinaison de bonus d'achat trouvée pour {budget}$"
            #                     break
            #             if combination_found:
            #                 break

            #         if not combination_found:
            #             # 3. Chercher un bonus supérieur
            #             bonus_sup = bonuses.filter(amount__gt=budget).first()
            #             if bonus_sup:
            #                 bonus_sup.amount_to_be_paid -= budget
            #                 bonus_sup.save()
            #                 paid_bonuses = [str(bonus_sup.id)]
            #                 message = f"Bonus d'achat réduit de {budget}$"
            #             else:
            #                 return Response(
            #                     {"error": "Aucun bonus d'achat produit disponible pour ce montant"}, 
            #                     status=status.HTTP_400_BAD_REQUEST
            #                 )

            #     # Créer l'enregistrement du paiement
            #     payment = Payment.objects.create(
            #         office=office_instance,
            #         account=account_instance,
            #         amount=budget,
            #         payment_type='purchase_payment',
            #         bonuses=paid_bonuses
            #     )

            #     return Response({
            #         "message": message,
            #         "payment": PaymentSerializer(payment).data
            #     }, status=status.HTTP_201_CREATED)

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
        "payment": PaymentSerializer(payment).data
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

        downline_data = [
            {
                "id": account.id,
                "full_name": f"{account.member.first_name} {account.member.last_name}",
                "company_id": account.company_id,
                "descendant_count": account.get_descendants(include_self=False).count()
            }
            for account in account_instance.get_descendants(include_self=True).order_by('created_at')
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

        referral_queryset = Referral.objects.filter(grantee=account_instance).order_by('is_paid')

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

        matching_queryset = Matching.objects.filter(grantee=account_instance).order_by('is_paid')

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

        purchase_bonus_queryset = PurchaseBonus.objects.filter(grantee=account_instance).order_by('is_paid')

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
