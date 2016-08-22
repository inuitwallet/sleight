import json
import logging

from channels import Channel
from channels import Group

from sleight.models import Order, Trade

log = logging.getLogger(__name__)


def check_trades(message):
    """
    Run as background task whenever an order is placed
    check the opposite type, top order for a match and trade if possible
    message contains the order that was placed
    """
    initiating_order = Order.objects.get(id=message.content['order_id'])

    # fetch the order of interest
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
    Group(
        'ws-{}-{}'.format(
            initiating_order.pair.base_currency.code.lower(),
            initiating_order.pair.relative_currency.code.lower(),
        )
    ).send({
        'text': json.dumps(
            {
                'order_id': initiating_order.id,
                'amount': float(str(initiating_order.amount)),
                'price': float(str(initiating_order.price)),
                'order_type': initiating_order.order_type,
                'state': initiating_order.state,
            }
        )
    })
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
            # update initiating order
            initiating_order.amount -= existing_order.amount
            initiating_order.state = 'partial'
            initiating_order.save()
            # update existing order
            existing_order.amount = 0
            existing_order.state = 'complete'
            existing_order.save()

        if initiating_order.amount == existing_order.amount:
            # Trade is full trade
            trade.partial = False
            trade.save()
            # update initiating order
            initiating_order.amount = 0
            initiating_order.state = 'complete'
            initiating_order.save()
            # update existing order
            existing_order.amount = 0
            existing_order.state = 'complete'
            existing_order.save()

        if initiating_order.amount < existing_order.amount:
            # Trade is partial trade
            trade.partial = True
            trade.save()
            # update existing order
            existing_order.amount -= initiating_order.amount
            existing_order.state = 'partial'
            existing_order.save()
            # update initiating order
            initiating_order.amount = 0
            initiating_order.state = 'complete'
            initiating_order.save()

        # if there are funds left in the initiating order, go again
        if initiating_order.amount > 0:
            order_data = {
                'order_id': initiating_order.id
            }
            print(message.channel)
            Channel('{}'.format(message.channel)).send(order_data)