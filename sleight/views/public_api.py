import time

import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import JsonResponse
from django.views.generic import View

from sleight.models import Order, CurrencyPair, Trade


class GetOrderBook(View):
    """
    Show open and partial orders on the books for the supplied pair.
    """

    @staticmethod
    def get(request, base_currency, relative_currency):
        # parse out the pair
        try:
            pair = CurrencyPair.objects.get(
                base_currency__code__iexact=base_currency,
                relative_currency__code__iexact=relative_currency
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {'success': False, 'message': {'pair': ['pair not found']}}
            )
        bid_orders = Order.objects.exclude(
            state='cancelled'
        ).exclude(
            state='complete'
        ).filter(
            pair=pair,
            order_type='bid'
        ).order_by(
            'price'
        )
        ask_orders = Order.objects.exclude(
            state='cancelled'
        ).exclude(
            state='complete'
        ).filter(
            pair=pair,
            order_type='ask'
        ).order_by(
            '-price'
        )
        return JsonResponse(
            {
                'success': True,
                'message': {
                    'bid_orders': [
                        {
                            'order_id': order.id,
                            'order_type': order.order_type,
                            'amount': order.amount,
                            'original_amount': order.original_amount,
                            'price': order.price,
                            'state': order.state,
                            'pair': '{}/{}'.format(
                                order.pair.base_currency.code.lower(),
                                order.pair.relative_currency.code.lower()
                            )
                        }
                        for order in bid_orders
                    ],
                    'ask_orders': [
                        {
                            'order_id': order.id,
                            'order_type': order.order_type,
                            'amount': order.amount,
                            'original_amount': order.original_amount,
                            'price': order.price,
                            'state': order.state,
                            'pair': '{}/{}'.format(
                                order.pair.base_currency.code.lower(),
                                order.pair.relative_currency.code.lower()
                            )
                        }
                        for order in ask_orders
                        ]
                }
            }
        )

    @staticmethod
    def post(request):
        return JsonResponse({'success': False, 'message': {'HTTP Method': ['Use GET']}})


class GetTicker(View):
    """
    Return a ticker for the chosen pair
    Sample response
        "btc/usnbt": {
            "last_trade_price": "0.00000035",
            "lowest_ask_price": "0.00000036",
            "highest_bid_price": "0.00000035",
            "base_volume": "0.15543370",
            "relative_volume": "512450.46072496",
            "24_hour_high": "0.00000036",
            "24_hour_low": "0.00000021"
        },
    """
    @staticmethod
    def get(request, base_currency, relative_currency):
        # parse out the pair
        try:
            pair = CurrencyPair.objects.get(
                base_currency__code__iexact=base_currency,
                relative_currency__code__iexact=relative_currency
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {'success': False, 'message': {'pair': ['pair not found']}}
            )

        # get all trades in the last 24 hours
        day_trades = Trade.objects.filter(
            initiating_order__pair__base_currency__code__iexact=base_currency
        ).filter(
            time__gt=datetime.datetime.fromtimestamp(time.time() - 86400)
        ).order_by(
            '-time'
        )

        # get the last trade price
        try:
            last_trade_price = day_trades[0].existing_order.price
            day_high = last_trade_price
            day_low = last_trade_price
        except IndexError:
            last_trade_price = None
            day_high = 0
            day_low = 0
        # get the highest and lowest trade prices
        for trade in day_trades:
            trade_price = trade.existing_order.price
            day_high = trade_price if trade_price > day_high else day_high
            day_low = trade_price if trade_price < day_low else day_low

        # get all open and partial ask orders
        all_asks = Order.objects.exclude(
            state='cancelled'
        ).exclude(
            state='complete'
        ).filter(
            pair=pair,
            order_type='ask'
        ).order_by(
            '-price'
        )
        # get the lowest ask price
        try:
            bottom_ask_price = all_asks[0].price
        except IndexError:
            bottom_ask_price = None
        # sum the volume
        ask_volume = 0
        for order in all_asks:
            ask_volume += order.amount

        # get all open and partial bid orders
        all_bids = Order.objects.exclude(
            state='cancelled'
        ).exclude(
            state='complete'
        ).filter(
            pair=pair,
            order_type='bid'
        ).order_by(
            'price'
        )
        # get the lowest bd price
        try:
            top_bid_price = all_bids[0].price
        except IndexError:
            top_bid_price = None
        # calculate the bid volume
        bid_volume = 0
        for order in all_bids:
            bid_volume += order.amount
        return JsonResponse(
            {
                'success': True,
                'message': {
                    'ticker': [
                        {
                            'last_trade_price': last_trade_price,
                            'lowest_ask_price': bottom_ask_price,
                            'highest_bid_price': top_bid_price,
                            'bid_volume': bid_volume,
                            'ask_volume': ask_volume,
                            '24_hour_high': day_high,
                            '24_hour_low': day_low
                        }
                    ]
                }
            }
        )

    @staticmethod
    def post(request):
        return JsonResponse(
            {'success': False, 'message': {'HTTP Method': ['Use GET']}})
