from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Referral,Matching
from .serializers import ReferralSerializer,MatchingSerializer


class ReferralViewSet(viewsets.ModelViewSet) :
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]


class MatchingViewSet(viewsets.ModelViewSet) :
    queryset = Matching.objects.all()
    serializer_class = MatchingSerializer
    permission_classes = [IsAuthenticated]
