from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Referral,Matching
from .serializers import ReferralSerializer, MatchingSerializer
from django_filters.rest_framework import DjangoFilterBackend
from .filters import MatchingFilter, ReferralFilter


class ReferralViewSet(viewsets.ModelViewSet) :
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]

    # Ajouter les backends pour le filtrage
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReferralFilter


class MatchingViewSet(viewsets.ModelViewSet) :
    queryset = Matching.objects.filter(is_validated=True)
    serializer_class = MatchingSerializer
    permission_classes = [IsAuthenticated]

    # Ajouter les backends pour le filtrage
    filter_backends = [DjangoFilterBackend]
    filterset_class = MatchingFilter