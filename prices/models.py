import uuid
from django.db import models
from django.utils.translation import gettext as _



class Referral(models.Model) :
    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    grantee = models.ForeignKey("members.Account", verbose_name=_("Grantee account"), related_name="referrals", on_delete=models.CASCADE)
    downline = models.ForeignKey("members.Account", verbose_name=_("Downline account"), on_delete=models.CASCADE)
    amount = models.DecimalField(_('Referral amount'), max_digits=6, decimal_places=2)
    created_at = models.DateField(_('Refer date'), auto_now_add=True)

    def __str__(self) -> str:
        return self.grantee.member.first_name +" "+self.grantee.member.last_name



class Matching(models.Model) :
    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    grantee = models.ForeignKey("members.Account", verbose_name=_("Grantee account"), related_name="grandee", on_delete=models.CASCADE)
    downlines = models.ManyToManyField("members.Account", verbose_name=_("Downline accounts"), related_name="downlines")
    amount = models.DecimalField(_('Referral amount'), max_digits=6, decimal_places=2)
    validated = models.BooleanField(default=False)
    created_at = models.DateField(_('Refer date'), auto_now_add=True)


    def __str__(self) -> str:
        return self.grantee.member.first_name +" "+self.grantee.member.last_name



class Reward(models.Model) :
    pass



class PurchaseBonus(models.Model) :
    pass



class Payment(models.Model):
    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("members.Account", verbose_name=_("Grantee account"), related_name="payments", on_delete=models.CASCADE)
    amount = models.DecimalField(_('Amount'), max_digits=6, decimal_places=2)
    created_at = models.DateField(_('Paid on'), auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.client.name} on {self.paid_on}"