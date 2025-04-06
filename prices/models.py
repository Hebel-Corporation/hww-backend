import uuid
from django.db import models
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey



class BonusBaseModel(models.Model):
    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    grantee = models.ForeignKey("members.Account", verbose_name=_("Grantee account"), on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True


    def __str__(self) -> str:
        return self.grantee.member.company_id



class Referral(BonusBaseModel) :
    downline = models.ForeignKey("members.Account", related_name="referral_downline", null=True, on_delete=models.CASCADE)



class Matching(BonusBaseModel) :
    downlines = models.ManyToManyField("members.Account", related_name="matching_downlines")
    is_validated = models.BooleanField(default=False)



class PurchaseBonus(BonusBaseModel) :
    sale_detail = models.ForeignKey("stock.SaleDetail", related_name="purchase_bonuses", null=True, on_delete=models.SET_NULL)
    amount_to_be_paid = models.DecimalField(max_digits=6, decimal_places=2, default=0)


    class Meta:
        verbose_name_plural = "Purchase bonuses"

    def save(self, *args, **kwargs):
        if not self.amount_to_be_paid:
            self.amount_to_be_paid = self.amount
        super().save(*args, **kwargs)


class Reward(models.Model) :
    pass





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
