from django.http.response import JsonResponse
from django.shortcuts import render, get_object_or_404

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
    try:
        base_balance = Balance.objects.get(
            user=request.user,
            currency=pair.base_currency
        )
    except Balance.DoesNotExist:
        base_balance = None
    try:
        relative_balance = Balance.objects.get(
            user=request.user,
            currency=pair.relative_currency
        )
    except Balance.DoesNotExist:
        base_balance = None
    context = {
        'pair': pair,
        'bids': bid_orders,
        'asks': ask_orders,
        'trades': trades,
        'base_balance': base_balance,
        'relative_balance': relative_balance,
    }
    return render(request, 'sleight/exchange.html', context)