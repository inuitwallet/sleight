from django import forms
from .utils import get_all_pairs


class BaseForm(forms.Form):
    nonce = forms.IntegerField(
        required=True,
    )
    api_key = forms.UUIDField(
        required=True,
        error_messages={
            'invalid': 'api_key not valid',
        },
    )
    nonce_hash = forms.CharField(
        max_length=64,
        required=True,
    )


class GetBalanceForm(BaseForm):
    pass


class PlaceOrderForm(BaseForm):
    order_type = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'form-control'}
        ),
        choices=[('bid', 'Bid'), ('ask', 'Ask')],
        error_messages={
            'invalid_choice': '%(value)s is not a valid order type. '
                              'Choose from \'bid\' or \'ask\''
        }
    )
    pair = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'form-control'}
        ),
        choices=get_all_pairs(),
        error_messages={
            'invalid_choice': '%(value)s is not a valid currency pair. '
                              'Choose from {}'.format(
                                  [pair[0] for pair in get_all_pairs()]
                              )
        }
    )
    amount = forms.DecimalField(
        widget=forms.NumberInput(
            attrs={'class': 'form-control'}
        ),
        max_digits=20,
        decimal_places=10,
    )
    price = forms.DecimalField(
        widget=forms.NumberInput(
            attrs={'class': 'form-control'}
        ),
        max_digits=20,
        decimal_places=10,
    )


class GetOrdersForm(BaseForm):
    pass


class CancelOrderForm(BaseForm):
    order_id = forms.IntegerField()
