from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    api_key = models.UUIDField(
        default=uuid.uuid4,
    )
    api_secret = models.UUIDField(
        default=uuid.uuid4,
    )
    nonce = models.BigIntegerField()

    def __str__(self):
        return self.user.email


class Currency(models.Model):
    name = models.CharField(
        max_length=255,
    )
    code = models.CharField(
        max_length=10,
        unique=True,
    )

    def __str__(self):
        return self.name

    class Meta(object):
        unique_together = ('name', 'code')


class CurrencyPair(models.Model):
    base_currency = models.ForeignKey(
        Currency,
        related_name='base_currency',
    )
    relative_currency = models.ForeignKey(
        Currency,
        related_name='relative_currency',
    )

    def __str__(self):
        return '{}/{}'.format(self.base_currency, self.relative_currency)

    class Meta(object):
        unique_together = ('base_currency', 'relative_currency')


class Order(models.Model):
    user = models.ForeignKey(
        User
    )
    pair = models.ForeignKey(
        CurrencyPair,
        related_name='order'
    )
    original_amount = models.DecimalField(
        max_digits=20,
        decimal_places=10,
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=10,
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=10,
    )
    order_type = models.CharField(
        choices=[('bid', 'Bid'), ('ask', 'Ask')],
        max_length=3
    )
    state = models.CharField(
        choices=[
            ('open', 'Open'),
            ('partial', 'Partial'),
            ('complete', 'Complete'),
            ('cancelled', 'Cancelled')
        ],
        max_length=15
    )
    time = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return '{}'.format(self.id)


class Trade(models.Model):
    initiating_order = models.ForeignKey(
        Order,
        related_name='initiating_order'
    )
    existing_order = models.ForeignKey(
        Order,
        related_name='existing_order'
    )
    time = models.DateTimeField(
        auto_now_add=True,
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=10,
    )
    partial = models.BooleanField()

    def __str__(self):
        return '{}'.format(self.time)


class Balance(models.Model):
    user = models.ForeignKey(
        User
    )
    currency = models.ForeignKey(
        Currency
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=10,
    )

    def __str__(self):
        return '{} {}'.format(self.currency, self.amount)
