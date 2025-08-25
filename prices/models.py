import uuid
from django.db import models
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Q, Sum
from utils.utils_functions import check_all_rewards, check_all_promotions
from django.utils import timezone


class BonusBaseModel(models.Model):
    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    grantee = models.ForeignKey("members.Account", verbose_name=_("Grantee account"), on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    office = models.ForeignKey("members.Office", null=True, on_delete=models.SET_NULL)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True


    def __str__(self) -> str:
        return self.grantee.member.company_id



class Referral(BonusBaseModel) :
    downline = models.ForeignKey("members.Account", related_name="referral_downline", null=True, on_delete=models.CASCADE)


    def save(self, *args, **kwargs):
        if self._state.adding :
            # Check if the member qualifies for a reward after creating a matching for him.
            check_all_rewards(self.grantee)
            check_all_promotions(self.grantee)

        super(Referral, self).save(*args, **kwargs)



class Matching(BonusBaseModel) :
    downlines = models.ManyToManyField("members.Account", related_name="matching_downlines")
    is_validated = models.BooleanField(default=True)



class PurchaseBonus(BonusBaseModel) :
    sale_detail = models.ForeignKey("stock.SaleDetail", related_name="purchase_bonuses", null=True, on_delete=models.CASCADE)
    amount_to_be_paid = models.DecimalField(max_digits=6, decimal_places=2, default=0)


    class Meta:
        verbose_name_plural = "Purchase bonuses"



class Gift(models.Model) :
    id = models.UUIDField("_ID", primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='gifts', null=True, blank=True)
    mark = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self) -> str:
        return self.name



class RewardBase(models.Model) :

    id = models.UUIDField("_ID", primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class RewardCommonFields(models.Model) :
    UNITS_TYPE = (
        ('matching', 'Equilibres'),
        ('referral', 'Parrainages')
    )

    id = models.UUIDField("_ID", primary_key=True, default=uuid.uuid4, editable=False)
    equivalent_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    unit_number = models.IntegerField(null=True, blank=True)
    unit_type = models.CharField(max_length=50, choices=UNITS_TYPE, null=True, blank=True)
    gift = models.ForeignKey("prices.Gift", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True


class PromotionItem(RewardCommonFields) :
    promotion = models.ForeignKey("prices.Promotion", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return self.gift.name



class Reward(RewardBase, RewardCommonFields) :

    def __str__(self) -> str:
        return str(self.title)

    
    @property
    def get_reward_qualification_count(self):
        return self.account_rewards.all().count()





class Promotion(RewardBase) :
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.start_date.strftime('%Y-%m-%d') + " - " + self.end_date.strftime('%Y-%m-%d')


    def save(self, *args, **kwargs):
        if self.is_active:
            # Désactive toutes les autres promotions actives
            Promotion.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=[],
    #             condition=Q(is_active=True),
    #             name="only_one_active_promotion"
    #         )
    #     ]


    @property
    def get_promotionItem_qualification_bonus_count(self):
        from members.models import Account
        count = 0
        
        for promoItem in self.promotionitem_set.all():
            # Pour chaque compte qui a qualifié pour cette promotion item
            for account in promoItem.account_promotions.all():
                if promoItem.unit_type == 'matching':
                    # Compter les matchings créés pendant la période de promotion
                    matching_count = Matching.objects.filter(
                        grantee=account,
                        created_at__range=(self.start_date, self.end_date),
                        is_validated=True
                    ).count()
                    count += matching_count
                    
                elif promoItem.unit_type == 'referral':
                    # Compter les referrals créés pendant la période de promotion
                    referral_count = Referral.objects.filter(
                        grantee=account,
                        created_at__range=(self.start_date, self.end_date)
                    ).count()
                    count += referral_count
                    
                elif promoItem.unit_type == 'purchase_bonus':
                    # Compter les bonus d'achat créés pendant la période de promotion
                    purchase_bonus_count = PurchaseBonus.objects.filter(
                        grantee=account,
                        created_at__range=(self.start_date, self.end_date)
                    ).count()
                    count += purchase_bonus_count
                    
        return count
    

    @property
    def get_account_qualification_count(self):
        return sum(item.account_promotions.count() for item in self.promotionitem_set.all())

    


class Payment(models.Model):

    PAYMENT_TYPE_CHOICES = (
        ('matching_payment', "Paiement d'équilibres"),
        ('referral_payment', "Paiement de parrainages"),
        ('purchase_payment', "Paiement de bonus d'achat produit"),
    )

    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("members.Account", verbose_name=_("Grantee account"), related_name="payments", on_delete=models.CASCADE)
    amount = models.DecimalField(_('Amount'), max_digits=6, decimal_places=2)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, null=True)
    bonuses = models.JSONField(default=list)
    office = models.ForeignKey("members.Office", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(_('Paid on'), auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.account.member.first_name} on {self.created_at}"
