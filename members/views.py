# from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated
# from members.models import *
# from .serializers import *


# class OfficeViewSet(viewsets.ModelViewSet) :
#     queryset = Office.objects.all()
#     serializer_class = OfficeSerializer
#     permission_classes = [IsAuthenticated]



# class PackageViewSet(viewsets.ModelViewSet) :
#     queryset = Package.objects.all()
#     serializer_class = PackageSerializer
#     permission_classes = [IsAuthenticated]



# class MemberViewSet(viewsets.ModelViewSet) :
#     queryset = Member.objects.all()
#     serializer_class = MemberSerializer
#     permission_classes = [IsAuthenticated]



# class AccountViewSet(viewsets.ModelViewSet) :
#     queryset = Account.objects.all()
#     serializer_class = AccountSerializer
#     permission_classes = [IsAuthenticated]



# class SubscriptionViewSet(viewsets.ModelViewSet) :
#     queryset = Subscription.objects.all()
#     serializer_class = SubscriptionSerializer
#     permission_classes = [IsAuthenticated]