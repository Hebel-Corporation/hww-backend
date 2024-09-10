import uuid
from django.db import models, transaction
from django.utils.translation import gettext as _
# from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from prices.models import Referral
from config.models import SubscriptionCode

from decimal import Decimal
from utils.utils_functions import create_pairing_bonuses


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
    position = models.CharField(_("Position at Sponsor"), choices=POSITION, default='left', max_length=10,editable=False)
    office = models.ForeignKey('members.Office', verbose_name=_("Account Office Recorder"), related_name="account_offices_set", blank=True, null=True, on_delete=models.SET_NULL)
    rewards = models.ManyToManyField("prices.Reward", verbose_name=_("Account rewards"), blank=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    created_at = models.DateField(_("Date"), auto_now=False, auto_now_add=True)


    class MPTTMeta:
        order_insertion_by = ['created_at']

    @transaction.atomic
    def save(self, *args, **kwargs):

        package_id = kwargs.pop('package_id', None)
  
        if self._state.adding :

            package = None

            if package_id :
                try :
                    package = Package.objects.get(id=package_id)
                except Package.DoesNotExist :
                    raise ValueError(f"Package with ID {package_id} does not exist.")
            else :
                package = Package.objects.filter(is_default=True).first() 

            subscription = Subscription.objects.create(
                office = self.office,
                package = package,
                member_account = self
            )
            subscription.save()

            # Creaing matchings if possible
            create_pairing_bonuses(new_member_account=self, upline=self.parent, position=self.position)

        super(Account, self).save(*args, **kwargs)



    def __str__(self) -> str:
        return self.company_id
    


class Subscription(models.Model) :
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    office = models.ForeignKey(Office, verbose_name=_("Office Creator"), related_name="subscriptions", null=True, on_delete=models.SET_NULL)
    package = models.ForeignKey(Package, verbose_name=_("Package"), null=True, on_delete=models.SET_NULL)
    member_account = models.ForeignKey(Account, verbose_name=_("Member account"), null=True, on_delete=models.SET_NULL)
    subscription_code = models.ForeignKey(SubscriptionCode, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(_('Created on'), auto_now_add=True)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self._state.adding and Referral.objects.all().count() >= 1 :

            referral_price = Referral.objects.create(
                grantee = self.member_account.referral_account,
                downline = self.member_account,
                amount = self.package.price * Decimal('0.2') # 20% du prix du package
            )
            referral_price.save()


        super(Subscription, self).save(*args, **kwargs)



    def __str__(self) -> str:
        return self.office.office_code
    
