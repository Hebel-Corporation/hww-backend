import uuid
from django.db import models, transaction
from django.utils.translation import gettext as _
# from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from prices.models import Referral, Matching, MemberPurchase
from config.models import SubscriptionCode

from decimal import Decimal
from utils.utils_functions import create_pairing_bonuses
from django.contrib.contenttypes.models import ContentType


class Country(models.Model) :

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("code"), max_length=5, null=True, blank=True)
    created_at = models.DateField(_("Date"), auto_now=False, auto_now_add=True)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['created_at']  # Default ordering of query results
        #db_table = 'my_custom_model_table'  # Custom table name in the database
        #unique_together = ['name', 'code']  # Ensure (name, code) pairs are unique
    

    def __str__(self) -> str:
        return self.name
    

class Location(models.Model) :

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=50)
    country = models.ForeignKey(Country, verbose_name=_("Location Country"), on_delete=models.CASCADE)
    created_at = models.DateField(_("Date"), auto_now=False, auto_now_add=True)
    

    def __str__(self) -> str:
        return self.name



class Office(models.Model) :
    OFFICE_TYPE = (
        ('head_office', 'Head Office'),
        ('sub_office', 'Sub Office')
    )

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=50, null=True, blank=True)
    office_code = models.CharField(_("Office Code"), max_length=50, unique=True, editable=False)
    location = models.ForeignKey(Location, related_name="offices", on_delete=models.SET_NULL, null=True)
    office_type = models.CharField(_("Office type"), choices=OFFICE_TYPE, default='sub_office', max_length=20)
    is_active = models.BooleanField(_('Is active'), default=True)
    created_at = models.DateField(_("Date"), auto_now_add=True)
    

    def __str__(self) -> str:
        return f"{self.location.name} - {self.office_code}"



class Package(models.Model) :
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=50)
    price = models.DecimalField(_('Price'), max_digits=6, decimal_places=2)
    is_default = models.BooleanField(null=True, blank=True, unique=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    


class Account(MPTTModel) :

    POSITION = (
        ('left', 'Left'),
        ('right', 'Right')
    )

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey("authentication.CustomUser", verbose_name=_("Member"), related_name="accounts", on_delete=models.CASCADE)
    company_id = models.CharField(_("Company ID"), max_length=50,unique=True)
    referral_account = models.ForeignKey('self', verbose_name=_("Referral account"), null=True, blank=True, on_delete=models.SET_NULL)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    position = models.CharField(_("Position at Sponsor"), choices=POSITION, default='left', null=True, blank=True, max_length=10, editable=False)
    # pvs = models.IntegerField(editable=False)
    office = models.ForeignKey('members.Office', verbose_name=_("Account Office Recorder"), related_name="account_offices_set", blank=True, null=True, on_delete=models.SET_NULL)
    rewards = models.ManyToManyField("prices.Reward", verbose_name=_("Account rewards"), blank=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    created_at = models.DateField(_("Date"), auto_now=False, auto_now_add=True)


    class MPTTMeta:
        order_insertion_by = ['created_at']

    @transaction.atomic
    def save(self, *args, **kwargs):

        subscription_code = kwargs.pop('subscription_code', None)
        is_new = self._state.adding
  
        if is_new :

            subscription = Subscription.objects.create(
                office = self.office,
                package = subscription_code.package,
                member_account = self,
                subscription_code =  subscription_code
            )
            subscription.save()

            # Increament subscription used code 
            if (subscription_code.used_reccords_number+1 >= subscription_code.reccords_number):
                subscription_code.is_valid = False
            
            subscription_code.used_reccords_number += 1
            subscription_code.save()


        super(Account, self).save(*args, **kwargs)

        if is_new :
            # Creaing matchings if possible
            create_pairing_bonuses(new_member_account=self, upline=self.parent, position=self.position)


    @property
    def get_matching_count(self):
        return Matching.objects.filter(grantee=self).count()


    @property
    def get_referral_count(self):
        return Referral.objects.filter(grantee=self).count()
    

    @property
    def get_puchase_bonus_count(self):
        return MemberPurchase.objects.filter(grantee=self).count()
    

    def has_already_a_matched(self, downline):
        return Matching.objects.filter(grantee=self, downlines__in=[downline]).exists()

    @property
    def get_pvs(self):
        subcriptions = Subscription.objects.filter(member_account__in=self.get_descendants(include_self=True).order_by('created_at'))
        pvs = 0
        for subcription in subcriptions :
            pvs += subcription.package.price

        return pvs



    @property
    def get_balance(self):
        referrals = Referral.objects.filter(grantee=self, is_paid=False) # Récupérer les referrals associés à un compte
        matchings = Matching.objects.filter(grantee=self, is_paid=False) # Récupérer les matchings associés à un compte
        purchase_bonus = MemberPurchase.objects.filter(grantee=self, is_paid=False) # Récupérer les bonus sur achat des produits à un compte

        # Combiner les résultats
        all_bonuses = list(referrals) + list(matchings) + list(purchase_bonus)
        balance = 0
        for bonus in all_bonuses :
            balance += bonus.amount

        return balance


    def __str__(self) -> str:
        return self.company_id
    


class Subscription(models.Model) :
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    office = models.ForeignKey(Office, verbose_name=_("Office Creator"), related_name="subscriptions", null=True, on_delete=models.SET_NULL)
    package = models.ForeignKey(Package, verbose_name=_("Package"), null=True, on_delete=models.SET_NULL)
    member_account = models.ForeignKey(Account, verbose_name=_("Member account"), null=True, on_delete=models.CASCADE)
    subscription_code = models.ForeignKey(SubscriptionCode, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(_('Created on'), auto_now_add=True)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self._state.adding and Account.objects.count() >= 1 :

            referral_price = Referral.objects.create(
                grantee = self.member_account.referral_account,
                downline = self.member_account,
                amount = self.package.price * Decimal('0.2') # 20% du prix du package
            )
            referral_price.save()


        super(Subscription, self).save(*args, **kwargs)



    def __str__(self) -> str:
        return self.office.office_code
    
