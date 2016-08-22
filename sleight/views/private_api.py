from channels import Channel
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import JsonResponse
from django.views.generic import View

from sleight.forms import GetBalanceForm, PlaceOrderForm, GetOrdersForm, CancelOrderForm, \
    GetTradesForm
from sleight.models import Balance, CurrencyPair, Order, Trade
from sleight.utils import ensure_valid


class GetBalances(View):
    """
    return the currency balances available to the authenticated user
    """

    @staticmethod
    def get(request):
        return JsonResponse({'success': False, 'message': {'HTTP Method': ['Use POST']}})

    @staticmethod
    def post(request):
        form = GetBalanceForm(request.POST)

        if form.is_valid():
            profile, message = ensure_valid(form.cleaned_data)
            if not profile:
                return JsonResponse({'success': False, 'message': message})

            # get the balances associated with the profile user
            balances = (
                Balance.objects.select_related(
                    'currency'
                ).filter(
                    user=profile.user
                )
            )

            return JsonResponse(
                {
                    'success': True,
                    'message': [
                        {
                            'currency_code': balance.currency.code,
                            'currency_name': balance.currency.name,
                            'amount': balance.amount
                        }
                        for balance in balances
                    ]
                }
            )

        else:
            return JsonResponse({'success': False, 'message': form.errors})


class PlaceOrder(View):
    """
    Allow an authenticated user to place an order
    """

    @staticmethod
    def get(request):
        return JsonResponse({'success': False, 'message': {'HTTP Method': ['Use POST']}})

    @staticmethod
    def post(request):
        form = PlaceOrderForm(request.POST)

        if form.is_valid():
            profile, message = ensure_valid(form.cleaned_data)
            if not profile:
                return JsonResponse({'success': False, 'message': message})

            # parse out the pair
            form_pair = form.cleaned_data['pair'].split('/')
            pair = CurrencyPair.objects.select_related(
                'base_currency',
                'relative_currency'
            ).get(
                base_currency__code__iexact=form_pair[0],
                relative_currency__code__iexact=form_pair[1]
            )

            # check the user has available funds
            if form.cleaned_data['order_type'] == 'bid':
                balance, created = Balance.objects.get_or_create(
                    user=profile.user,
                    currency=pair.base_currency
                )
                if created:
                    balance.amount = 0
                    balance.save()

                if balance.amount < (form.cleaned_data['amount'] * form.cleaned_data['price']):
                    return JsonResponse(
                        {
                            'success': False,
                            'message': {
                                'insufficient balance': '{} {}'.format(
                                    balance,
                                    pair.base_currency.code.upper()
                                )
                            }
                        }
                    )

            else:
                balance, created = Balance.objects.get_or_create(
                    user=profile.user,
                    currency=pair.relative_currency
                )
                if created:
                    balance.amount = 0
                    balance.save()

                if balance.amount < form.cleaned_data['amount']:
                    return JsonResponse(
                        {
                            'success': False,
                            'message': {
                                'insufficient balance': '{} {}'.format(
                                    balance,
                                    pair.relative_currency.code.upper()
                                )
                            }
                        }
                    )

            # user has balance. reduce it by the amount of the order
            balance.amount -= form.cleaned_data['amount']
            balance.save()

            order = Order.objects.create(
                user=profile.user,
                order_type=form.cleaned_data['order_type'],
                pair=pair,
                original_amount=form.cleaned_data['amount'],
                amount=form.cleaned_data['amount'],
                price=form.cleaned_data['price'],
                state='open'
            )
            # order is placed.
            # Use channels to check for potential trades
            order_data = {
                'order_id': order.id
            }
            Channel(
                '{}-{}'.format(
                    pair.base_currency.code.lower(),
                    pair.relative_currency.code.lower(),
                )
            ).send(
                order_data
            )
            return JsonResponse(
                {
                    'success': True,
                    'message': {
                        'order_id': order.id
                    }
                }
            )
        else:
            return JsonResponse({'success': False, 'message': form.errors})


class GetOrders(View):
    """
    return all the orders for the authenticated user
    """

    @staticmethod
    def get(request):
        return JsonResponse({'success': False, 'message': {'HTTP Method': ['Use POST']}})

    @staticmethod
    def post(request):
        form = GetOrdersForm(request.POST)

        if form.is_valid():
            profile, message = ensure_valid(form.cleaned_data)
            if not profile:
                return JsonResponse({'success': False, 'message': message})

            # get the orders for the user
            orders = Order.objects.select_related('pair').filter(user=profile.user)
            return JsonResponse(
                {
                    'success': True,
                    'message': {
                        'orders': [
                            {
                                'id': order.id,
                                'state': order.state,
                                'amount': order.amount,
                                'original_amount': order.original_amount,
                                'price': order.price,
                                'order_type': order.order_type,
                                'pair': '{}/{}'.format(
                                    order.pair.base_currency.code.lower(),
                                    order.pair.relative_currency.code.lower()
                                ),
                            }
                            for order in orders
                        ]
                    }
                }
            )

        else:
            return JsonResponse({'success': False, 'message': form.errors})


class CancelOrder(View):
    """
    Allow an authenticated user to cancel an order by providing the order id
    """

    @staticmethod
    def get(request):
        return JsonResponse({'success': False, 'message': {'HTTP Method': ['Use POST']}})

    @staticmethod
    def post(request):
        form = CancelOrderForm(request.POST)

        if form.is_valid():
            profile, message = ensure_valid(form.cleaned_data)
            if not profile:
                return JsonResponse({'success': False, 'message': message})

            # get the order
            try:
                order = Order.objects.exclude(
                    state='cancelled'
                ).exclude(
                    state='complete'
                ).get(
                    id=form.cleaned_data['order_id'],
                    user=profile.user
                )
            except ObjectDoesNotExist:
                return JsonResponse(
                    {
                        'success': False,
                        'message': {
                            'order_id': 'cannot cancel order {}'.format(
                                form.cleaned_data['order_id']
                            )
                        }
                    }
                )
            order.state = 'cancelled'
            order.save()
            return JsonResponse(
                {
                    'success': True,
                    'message': {'order_cancelled': order.id}
                }
            )

        else:
            return JsonResponse({'success': False, 'message': form.errors})


class GetTrades(View):
    """
    Get all trades for an authenticated user
    """

    @staticmethod
    def get(request):
        return JsonResponse({'success': False, 'message': {'HTTP Method': ['Use POST']}})

    @staticmethod
    def post(request):
        form = GetTradesForm(request.POST)

        if form.is_valid():
            profile, message = ensure_valid(form.cleaned_data)
            if not profile:
                return JsonResponse({'success': False, 'message': message})

            trades = Trade.objects.filter(
                initiating_order__user=profile.user
            )
            return JsonResponse(
                {
                    'success': True,
                    'message': {
                        'trades': [
                            {
                                'id': trade.id,
                                'initiating_order': trade.initiating_order,
                                'existing_order': trade.existing_order,
                                'time': trade.time,
                                'amount': trade.amount,
                                'partial': trade.partial
                            }
                            for trade in trades
                            ]
                    }
                }
            )

        else:
            return JsonResponse({'success': False, 'message': form.errors})