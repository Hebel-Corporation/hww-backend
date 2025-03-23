from django.db import models, transaction
import uuid
from django.utils.translation import gettext as _
from decimal import Decimal

from prices.models import PurchaseBonus


class SaleDetail(models.Model):
    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    member_account = models.ForeignKey("members.Account", verbose_name=_("Member account"), on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    office = models.ForeignKey("members.Office", null=True, on_delete=models.SET_NULL)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)


    @transaction.atomic
    def save(self, *args, **kwargs):

        if self._state.adding :

            referral_price = PurchaseBonus.objects.create(
                grantee = self.member_account.referral_account,
                sale_detail = self,
                amount = self.amount * Decimal('0.4') # 40% du monant total des protuits
            )
            referral_price.save()

        super(SaleDetail, self).save(*args, **kwargs)



    def __str__(self) -> str:
        return self.member_account.member.company_id
