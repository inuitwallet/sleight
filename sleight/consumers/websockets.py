import logging

from channels import Group
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from sleight.models import CurrencyPair

log = logging.getLogger(__name__)


def ws_connect(message):
    # Get the prefix and requested currencies from the path
    try:
        prefix, base_currency, relative_currency = (
            message['path'].decode('ascii').strip('/').split('/')
        )
        # error if the socket hasn't requested an exchange
        if prefix != 'exchange':
            log.debug('invalid ws path=%s', message['path'])
            return
    except ValueError:
        log.debug('invalid ws path=%s', message['path'])
        return

    # check the requested pair
    try:
        CurrencyPair.objects.get(
            base_currency__code__iexact=base_currency,
            relative_currency__code__iexact=relative_currency
        )
    except CurrencyPair.DoesNotExist:
        log.debug('invalid pair {}/{}'.format(base_currency, relative_currency))
        return

    # add the sockets reply channel to the exchange group
    Group(
        'ws-{}-{}'.format(base_currency.lower(), relative_currency.lower()),
        channel_layer=message.channel_layer
    ).add(message.reply_channel)

    # also add the socket reply channel to a user group
    # first, get the session id from the message headers
    session_id = None
    for header in message['headers']:
        if header[0] == 'cookie':
            data = header[1].split(';')
            for datum in data:
                session_id_check = datum.strip().split('=')
                if session_id_check[0] == 'sessionid':
                    session_id = session_id_check[1]
    # if we got a session id, we add the reply channel to that users
    if session_id:
        session = Session.objects.get(session_key=session_id)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        Group(
            user.username,
            channel_layer=message.channel_layer
        ).add(message.reply_channel)



def ws_disconnect(message):
    # check every exchange channel and remove the reply channel
    # (discard removes if the channel exists in a group and nothing otherwise)
    for pair in CurrencyPair.objects.select_related(
            'base_currency',
            'relative_currency'
    ).all():
        Group(
            'ws-{}-{}'.format(
                pair.base_currency.code.lower(),
                pair.relative_currency.code.lower()
            )
        ).discard(message.reply_channel)
