from django.db import models, transaction
import uuid
from django.utils import timezone
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

        if self._state.adding:

            ref_date = timezone.now().date()
            is_first_in_month = not SaleDetail.objects.filter(
                member_account_id=self.member_account_id,
                created_at__year=ref_date.year,
                created_at__month=ref_date.month,
            ).exists()
            if is_first_in_month:
                # 10 USD: frais de maintenance du mois — le bonus parrain s’applique au reliquat (premier achat produit du mois seulement)
                bonus_base = self.amount - Decimal('10')
            else:
                bonus_base = self.amount

            if bonus_base > 0:
                calculated_amount = bonus_base * Decimal('0.4')
                PurchaseBonus.objects.create(
                    grantee=self.member_account.referral_account,
                    sale_detail=self,
                    amount=calculated_amount,
                    amount_to_be_paid=calculated_amount,
                    office=self.office
                )

        super(SaleDetail, self).save(*args, **kwargs)



    def __str__(self) -> str:
        return self.member_account.member.company_id
