from django.db import models

class MatchingPrice(models.Model):
    begin = models.IntegerField(default=0)
    end = models.IntegerField(default=0)
    package_price_percent = models.DecimalField(max_digits=6, decimal_places=3)
