from sleight.models import CurrencyPair


def get_all_pairs():
    pair_list = []
    pairs = CurrencyPair.objects.select_related(
        'base_currency',
        'relative_currency'
    ).all()
    for pair in pairs:
        this_pair = '{}/{}'.format(pair.base_currency.code, pair.relative_currency.code)
        pair_list.append((this_pair.lower(), this_pair))
    return pair_list