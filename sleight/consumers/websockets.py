import json
import logging

from channels import Group

from sleight.models import CurrencyPair, Order

log = logging.getLogger(__name__)


def ws_connect(message):
    # Extract the room from the message. This expects message.path to be of the
    # form /chat/{label}/, and finds a Room if the message path is applicable,
    # and if the Room exists. Otherwise, bails (meaning this is a some othersort
    # of websocket). So, this is effectively a version of _get_object_or_404.
    try:
        prefix, base_currency, relative_currency = (
            message['path'].decode('ascii').strip('/').split('/')
        )
        if prefix != 'exchange':
            log.debug('invalid ws path=%s', message['path'])
            return
    except ValueError:
        log.debug('invalid ws path=%s', message['path'])
        return

    # check the requested pair
    try:
        pair = CurrencyPair.objects.get(
            base_currency__code__iexact=base_currency,
            relative_currency__code__iexact=relative_currency
        )
    except CurrencyPair.DoesNotExist:
        log.debug('invalid pair {}/{}'.format(base_currency, relative_currency))
        return

    # Need to be explicit about the channel layer so that testability works
    # This may be a FIXME?
    Group(
        'ws-{}-{}'.format(base_currency.lower(), relative_currency.lower()),
        channel_layer=message.channel_layer
    ).add(message.reply_channel)

    log.info(
        'client added to ws-{}-{}'.format(
            base_currency.lower(),
            relative_currency.lower()
        )
    )


def ws_receive(message):
    if 'order_id' not in message.content:
        log.info('received message: {}'.format(message.content))
        return
    try:
        order = Order.objects.get(id=message.content['order_id'])
    except Order.DoesNotExist:
        log.debug('no order available')
        return

    data = {
        'text': {
            "order_id": order.id,
            "amount": float(str(order.amount)),
        }
    }

    log.info(
        'sending {} to ws-{}-{}'.format(
            data,
            order.pair.base_currency.code.lower(),
            order.pair.relative_currency.code.lower()
        )
    )

    Group(
        'ws-{}-{}'.format(
            order.pair.base_currency.code.lower(),
            order.pair.relative_currency.code.lower()
        ),
        channel_layer=message.channel_layer
    ).send(data)
