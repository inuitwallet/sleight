import hashlib
import hmac

from channels import Channel
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from sleight.models import Profile, Balance, Order, CurrencyPair, Trade
from .forms import GetBalanceForm, PlaceOrderForm, GetOrdersForm, CancelOrderForm


def index(request):
    return JsonResponse({'success': True, 'message': 'It Works!'})


def exchange(request, base_currency, relative_currency):
    """
    simple view to show orders on a pair
    """
    # get the pair
    pair = CurrencyPair.objects.get(
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
    )
    context = {
        'pair': pair,
        'bids': bid_orders,
        'asks': ask_orders,
        'trades': trades,
    }
    return render(request, 'sleight/exchange.html', context)


def ensure_valid(data):
    """
    make sure the api_key returns a valid profile
    ensure the nonce is bigger then the previous nonce
    ensure the hash of the nonce is valid given the users api_secret
    """
    # ensure api_key is valid
    try:
        profile = Profile.objects.select_related('user').get(api_key=data['api_key'])
    except ObjectDoesNotExist:
        return False, {'api_key': ['api_key not valid']}

    # ensure nonce is bigger than previous
    # TODO - re-enable this check
    #if profile.nonce >= data['nonce']:
    #    return False,
    #        {'nonce': ['nonce needs to be greater than {}'.format(profile.nonce)]}
    # save the nonce for the next request
    profile.nonce = data['nonce']
    profile.save()

    # ensure the secret hash of the nonce is correct
    calculated_hash = hmac.new(
        str(profile.api_secret),
        str(data['nonce']),
        hashlib.sha256
    ).hexdigest()
    if calculated_hash != data['nonce_hash']:
        return False, {'nonce_hash': ['nonce_hash is incorrect']}
    return profile, ''


class GetBalances(View):

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
                try:
                    balance = Balance.objects.get(
                        user=profile.user,
                        currency=pair.base_currency
                    )
                except ObjectDoesNotExist:
                    balance = 0

                if balance < (form.cleaned_data['amount'] * form.cleaned_data['price']):
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
            if form.cleaned_data['order_type'] == 'ask':
                try:
                    balance = Balance.objects.get(
                        user=profile.user,
                        currency=pair.relative_currency
                    )
                except ObjectDoesNotExist:
                    balance = 0

                if balance < form.cleaned_data['amount']:
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
            print(
                'sending {} to check-trades-{}-{}'.format(
                    order_data,
                    pair.base_currency.code.lower(),
                    pair.relative_currency.code.lower()
                )
            )
            Channel(
                'check-trades-{}-{}'.format(
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

