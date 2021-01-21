from django.db import models
from django.contrib.auth.models import User, auth
from datetime import datetime

# Create your models here.


class Stock(models.Model):
    ticker = models.CharField(max_length=10)  # change ticker to symbol later

    def __str__(self):
        return self.ticker


class Port_users(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.user_id


class Portfolio(models.Model):
    portfolio_id = models.ForeignKey(
        Port_users, on_delete=models.DO_NOTHING, default=1)
    portfolio = models.CharField(max_length=10, default='Welcome')
    portfolio_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.portfolio


class Port_stock(models.Model):
    port_id = models.ForeignKey(Portfolio, on_delete=models.DO_NOTHING)
    symbol = models.CharField(max_length=10, default='SOME STRING')

    def __str__(self):
        return self.symbol
