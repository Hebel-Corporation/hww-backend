from django_filters import rest_framework as filters
from .models import Matching, Referral, PurchaseBonus



class MatchingFilter(filters.FilterSet):
    is_paid = filters.BooleanFilter(field_name="is_paid", lookup_expr="exact")  # Filtrer exactement sur is_paid

    class Meta:
        model = Matching
        fields = ['is_paid']  # Liste des champs filtrables



class ReferralFilter(filters.FilterSet):
    is_paid = filters.BooleanFilter(field_name="is_paid", lookup_expr="exact")  # Filtrer exactement sur is_paid

    class Meta:
        model = Referral
        fields = ['is_paid']  # Liste des champs filtrables


# class PurchaseFilter(filters.FilterSet):
#     is_paid = filters.BooleanFilter(field_name="is_paid", lookup_expr="exact")  # Filtrer exactement sur is_paid

#     class Meta:
#         model = PurchaseBonus
#         fields = ['is_paid']  # Liste des champs filtrables
