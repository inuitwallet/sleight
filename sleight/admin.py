from django.contrib import admin

from .models import *


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'api_key', 'api_secret')

admin.site.register(Profile, ProfileAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

admin.site.register(Currency, CurrencyAdmin)

admin.site.register(CurrencyPair)


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'time', 'order_type', 'pair', 'amount', 'price', 'state'
    )

admin.site.register(Order, OrderAdmin)


class TradeAdmin(admin.ModelAdmin):
    list_display = ('time', 'initiating_order', 'existing_order', 'amount', 'partial')

admin.site.register(Trade, TradeAdmin)


class BalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'amount')

admin.site.register(Balance, BalanceAdmin)
