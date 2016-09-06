import json
import logging

import datetime

from channels import Channel
from channels import Group

from sleight.models import Order, Trade, Balance

log = logging.getLogger(__name__)


def update_order(order, new_amount):
    order.amount = new_amount
    if new_amount > 0:
        order.state = 'partial'
    else:
        order.state = 'complete'
    order.save()


def send_to_ws_group(group_name, data):
    Group(group_name).send({'text': json.dumps(data)})


def update_balance(user, currency, amount, order_type):
    # fetch the current balance objects for both users
    # ask/sell orders get the base currency
    # bid/buy orders get the variable currency
    balance, _ = Balance.objects.get_or_create(
        user=user,
        currency=currency
    )

    # update the balances accordingly
    # ask/sell order gets the initiating order amount
    # bid/buy order gets the initiating order amount * the price
    # update the balance on the front end
    log.info('initiating balance = {}'.format(balance))
    log.info('adding {}'.format(amount))
    balance.amount += amount
    balance.save()
    log.info('initiating balance = {}'.format(balance))
    send_to_ws_group(user.username, {
        'message_type': 'balance',
        'balance_type': (
            'base_balance'
            if order_type == 'ask' else
            'relative_balance'
        ),
        'balance': str(balance.amount)
    })


def check_trades(message):
    """
    Run as background task whenever an order is placed
    check the opposite type, top order for a match and trade if possible
    message contains the order that was placed
    """
    initiating_order = Order.objects.get(id=message.content['order_id'])
    log.info(
        'received {} order {}. Notifying group'.format(
            initiating_order.order_type,
            initiating_order.id
        )
    )
    group_name = 'ws-{}-{}'.format(
        initiating_order.pair.base_currency.code.lower(),
        initiating_order.pair.relative_currency.code.lower()
    )
    send_to_ws_group(group_name, {
        'message_type': 'order',
        'order_id': initiating_order.id,
        'amount': str(initiating_order.amount),
        'price': str(initiating_order.price),
        'order_type': initiating_order.order_type,
        'state': initiating_order.state,
    })
    # fetch the top order of interest
    # get highest bid or lowest ask
    existing_order = Order.objects.exclude(
        state='closed'
    ).exclude(
        state='cancelled'
    ).exclude(
        amount=0
    ).filter(
        order_type='bid' if initiating_order.order_type == 'ask' else 'ask',
        pair=initiating_order.pair
    ).order_by(
        '-price' if initiating_order.order_type == 'ask' else 'price',
    )[:1]

    try:
        existing_order = existing_order[0]
    except IndexError:
        log.error(
            'No {} orders on book to match'.format(
                'bid' if initiating_order.order_type == 'ask' else 'ask'
            )
        )
        return

    # given the order found, see if we can trade
    log.info(
        'checking {} {} {} on {} order'.format(
            initiating_order.price,
            '<=' if initiating_order.order_type == 'ask' else '>=',
            existing_order.price,
            initiating_order.order_type
        )
    )
    if initiating_order.price <= existing_order.price \
            if initiating_order.order_type == 'ask' \
            else initiating_order.price >= existing_order.price:
        trade = Trade(
            initiating_order=initiating_order,
            existing_order=existing_order,
            amount=initiating_order.amount,
        )
        log.info('trade initialised')
        # check the amounts to determine partial or full trade
        if initiating_order.amount > existing_order.amount:
            # Trade is full trade
            trade.partial = False
            trade.save()
            # given that we've traded, we need to update some balances and orders
            update_balance(
                user=initiating_order.user,
                currency=(
                    initiating_order.pair.base_currency
                    if initiating_order.order_type == 'ask' else
                    initiating_order.pair.relative_currency
                ),
                amount=(
                    (existing_order.amount * existing_order.price)
                    if initiating_order.order_type == 'ask' else
                    existing_order.amount
                ),
                order_type=initiating_order.order_type,
            )
            update_order(
                initiating_order,
                (initiating_order.amount - existing_order.amount)
            )
            update_balance(
                user=existing_order.user,
                currency=(
                    existing_order.pair.base_currency
                    if existing_order.order_type == 'ask' else
                    existing_order.pair.relative_currency
                ),
                amount=(
                    (existing_order.amount * existing_order.price)
                    if initiating_order.order_type == 'ask' else
                    existing_order.amount
                ),
                order_type=existing_order.order_type,
            )
            update_order(existing_order, 0)

        if initiating_order.amount == existing_order.amount:
            # Trade is full trade
            trade.partial = False
            trade.save()
            # given that we've traded, we need to update some balances and orders
            update_balance(
                user=initiating_order.user,
                currency=(
                    initiating_order.pair.base_currency
                    if initiating_order.order_type == 'ask' else
                    initiating_order.pair.relative_currency
                ),
                amount=(
                    (existing_order.amount * existing_order.price)
                    if initiating_order.order_type == 'ask' else
                    existing_order.amount
                ),
                order_type=initiating_order.order_type,
            )
            update_order(initiating_order, 0)
            update_balance(
                user=existing_order.user,
                currency=(
                    existing_order.pair.base_currency
                    if existing_order.order_type == 'ask' else
                    existing_order.pair.relative_currency
                ),
                amount=(
                    (existing_order.amount * existing_order.price)
                    if initiating_order.order_type == 'ask' else
                    existing_order.amount
                ),
                order_type=existing_order.order_type,
            )
            update_order(existing_order, 0)

        if initiating_order.amount < existing_order.amount:
            # Trade is partial trade
            trade.partial = True
            trade.save()
            # given that we've traded, we need to update some balances and orders
            update_balance(
                user=existing_order.user,
                currency=(
                    existing_order.pair.base_currency
                    if existing_order.order_type == 'ask' else
                    existing_order.pair.relative_currency
                ),
                amount=(
                    (initiating_order.amount * existing_order.price)
                    if existing_order.order_type == 'ask' else
                    initiating_order.amount
                ),
                order_type=existing_order.order_type,
            )
            update_order(
                existing_order,
                (existing_order.amount - initiating_order.amount)
            )
            update_balance(
                user=initiating_order.user,
                currency=(
                    initiating_order.pair.base_currency
                    if initiating_order.order_type == 'ask' else
                    initiating_order.pair.relative_currency
                ),
                amount=(
                    (initiating_order.amount * existing_order.price)
                    if existing_order.order_type == 'ask' else
                    initiating_order.amount
                ),
                order_type=initiating_order.order_type,
            )
            update_order(initiating_order, 0)

        # update the orders to the group
        send_to_ws_group(group_name, {
            'message_type': 'order',
            'order_id': initiating_order.id,
            'state': initiating_order.state,
            'amount': str(initiating_order.amount),
            'price': str(existing_order.price)
        })

        send_to_ws_group(group_name, {
            'message_type': 'order',
            'order_id': existing_order.id,
            'state': existing_order.state,
            'amount': str(existing_order.amount),
            'price': str(existing_order.price)
        })

        # send the trade too
        send_to_ws_group(group_name, {
            'message_type': 'trade',
            'trade_time': str(
                datetime.datetime.strftime(
                    trade.time,
                    '%Y-%m-%d %H:%M:%S %Z'
                )
            ),
            'trade_type': initiating_order.order_type,
            'amount': str(trade.amount),
            'price': str(existing_order.price),
            'initiating_id': str(initiating_order.id),
            'existing_id': str(existing_order.id)
        })

        # if there are funds left in the initiating order, go again
        if initiating_order.amount > 0:
            order_data = {
                'order_id': initiating_order.id
            }
            print(message.channel)
            Channel('{}'.format(message.channel)).send(order_data)

        log.info('trade check finished')
