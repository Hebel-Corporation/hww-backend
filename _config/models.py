from django.db import models
from utils.utils_functions import generate_subcription_code
from members.models import Package, Office


class SubscriptionCode(models.Model):
    code = models.CharField(max_length=100)
    reccords_number = models.IntegerField()
    equivalent_amount = models.FloatField(default=0.0)
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True)
    package = models.ForeignKey(Package, null=True, on_delete=models.SET_NULL)
    is_valid = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.id:
            self.code = generate_subcription_code()

        super(SubscriptionCode, self).save(*args, **kwargs)


    def __str__(self):
        return self.office.office_code