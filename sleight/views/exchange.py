from decimal import Decimal

from django.http.response import JsonResponse
from django.shortcuts import render, get_object_or_404
from graphos.renderers.gchart import LineChart
from graphos.sources.model import ModelDataSource

from sleight.models import CurrencyPair, Order, Trade, Balance


def index(request):
    return JsonResponse({'success': True, 'message': 'It Works!'})


def exchange(request, base_currency, relative_currency):
    """
    simple view to show orders on a pair
    """
    # get the pair
    pair = get_object_or_404(
        CurrencyPair,
        base_currency__code__iexact=base_currency,
        relative_currency__code__iexact=relative_currency
    )
    # get bid orders
    bid_orders = Order.objects.exclude(
        state='closed'
    ).exclude(
        state='cancelled'
    ).exclude(
        amount=0
    ).filter(
        order_type='bid',
        pair=pair,
    ).order_by(
        '-price',
    )
    # get ask orders
    ask_orders = Order.objects.exclude(
        state='closed'
    ).exclude(
        state='cancelled'
    ).exclude(
        amount=0
    ).filter(
        order_type='ask',
        pair=pair,
    ).order_by(
        'price',
    )
    # get trades
    trades = Trade.objects.select_related(
        'initiating_order',
        'existing_order'
    ).order_by(
        '-time'
    ).filter(
        initiating_order__pair=pair,
    )[:150]
    # get user balances
    if request.user.is_authenticated:
        base_balance, _ = Balance.objects.get_or_create(
            user=request.user,
            currency=pair.base_currency
        )
        relative_balance, _ = Balance.objects.get_or_create(
            user=request.user,
            currency=pair.relative_currency
        )
    else:
        base_balance = None
        relative_balance = None
    context = {
        'pair': pair,
        'bids': bid_orders,
        'asks': ask_orders,
        'trades': trades,
        'base_balance': base_balance,
        'relative_balance': relative_balance,
        'user': request.user,
    }
    return render(request, 'sleight/exchange.html', context)


def register(request):
    return JsonResponse({'yup': True})


def graph(request):
    orders = Order.objects.exclude(
        state='cancelled'
    ).exclude(
        state='complete'
    ).order_by(
        'price'
    )

    prices = sorted(list(set(list(
        float(order.price) for order in orders
    ))))

    order_totals = []
    for price in prices:
        this_total = {'ask': 0, 'bid': 0, 'price': price}
        for order in orders:
            if order.price == price:
                this_total[order.order_type] += order.amount
        order_totals.append(this_total)

    context = {
        'orders': list(
            [float(total['price']), float(total['ask']), float(total['bid'])]
            for total in order_totals
        )
    }
    return render(request, 'chart.html', context)
