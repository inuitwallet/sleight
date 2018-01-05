import codecs
import hashlib
import hmac

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from sleight.models import CurrencyPair, Profile


def get_all_pairs():
    pair_list = []
    if 'sleight_currencypair' not in connection.introspection.table_names():
        return pair_list
    pairs = CurrencyPair.objects.select_related(
        'base_currency',
        'relative_currency'
    ).all()
    for pair in pairs:
        this_pair = '{}/{}'.format(pair.base_currency.code, pair.relative_currency.code)
        pair_list.append((this_pair.lower(), this_pair))
    return pair_list


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
    if profile.nonce >= data['nonce']:
        return False, {
            'nonce': ['nonce needs to be greater than {}'.format(profile.nonce)]
        }
    # save the nonce for the next request
    profile.nonce = data['nonce']
    profile.save()

    # ensure the secret hash of the nonce is correct
    calculated_hash = hmac.new(
        '{}'.format(profile.api_secret).encode('utf-8'),
        '{}'.format(data['nonce']).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    if calculated_hash != data['nonce_hash']:
        return False, {'nonce_hash': ['nonce_hash is incorrect']}
    return profile, ''
