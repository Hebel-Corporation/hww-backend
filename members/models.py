import uuid
from django.db import models
from django.utils.translation import gettext as _
# from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from utils.userful_methods import on_account_save, on_office_save




class Country(models.Model) :

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("code"), max_length=5, null=True, blank=True)
    created_at = models.DateField(_("Date"), auto_now=False, auto_now_add=True)
    

    def __str__(self) -> str:
        return self.name
    

class Location(models.Model) :

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=50)
    country = models.ForeignKey(Country, verbose_name=_("Location Country"), on_delete=models.CASCADE)
    code = models.CharField(_("code"), max_length=5, null=True, blank=True)
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
    company_id = models.CharField(_("Office Code"), max_length=50, unique=True, editable=False)
    location = models.ForeignKey(Location, related_name="offices", on_delete=models.SET_NULL, null=True)
    office_type = models.CharField(_("Office type"), choices=OFFICE_TYPE, default='sub_office', max_length=20)
    is_active = models.BooleanField(_('Is active'), default=True)
    created_at = models.DateTimeField(_("Date"), auto_now=False, auto_now_add=True)
    

    def __str__(self) -> str:
        return self.name
    
    def save(self, *args, **kwargs):

        on_office_save(self)

        super(Office, self).save(*args, **kwargs)



class Package(models.Model) :
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=50)
    price = models.DecimalField(_('Price'), max_digits=6, decimal_places=2)
    is_default = models.BooleanField(null=True, blank=True, unique=True)
    description = models.TextField(_("Description"), null=True)
    created_at = models.DateField(_("Date"), auto_now=False, auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    


class Account(MPTTModel) :

    POSITION = (
        ('left', 'Left'),
        ('right', 'Right')
    )
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey("authentication.CustomUser", verbose_name=_("Member"), related_name="accounts", on_delete=models.CASCADE)
    company_id = models.CharField(_("Company ID"), max_length=50,unique=True,editable=False)
    package = models.ForeignKey(Package, verbose_name=_("Package"), null=True, on_delete=models.SET_NULL)
    referral_account = models.ForeignKey('self', verbose_name=_("Referral account"), null=True, blank=True, on_delete=models.SET_NULL)
    parent = TreeForeignKey('self',verbose_name=_("Sponsor account"), on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    position = models.CharField(_("Position at Sponsor"), choices=POSITION, default='left', max_length=10,editable=False)
    office = models.ForeignKey('members.Office', verbose_name=_("Account Office Recorder"), related_name="account_offices_set", blank=True, null=True, on_delete=models.SET_NULL)
    rewards = models.ManyToManyField("prices.Reward", verbose_name=_("Account rewards"), blank=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    created_at = models.DateTimeField(_("Date"), auto_now=False, auto_now_add=True)


    class MPTTMeta:
        order_insertion_by = ['created_at']

    # def get_parent(self):
    #     return self.sponsor_account

    # def set_parent(self, parent):
    #     self.sponsor_account = parent


    def save(self, *args, **kwargs):

        on_account_save(self)

        super(Account, self).save(*args, **kwargs)


    def __str__(self) -> str:
        return str(self.company_id)
    


class Subscription(models.Model) :
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    office = models.ForeignKey(Office, verbose_name=_("Office Creator"), related_name="subscriptions", null=True, on_delete=models.SET_NULL)
    member_account = models.ForeignKey(Account, verbose_name=_("Member account"), null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('Created on'), auto_now_add=True)


    def __str__(self) -> str:
        return self.member_account
    
