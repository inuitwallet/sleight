from channels import route
from consumers import check_trades

channel_routing = [
    route('btc-usnbt', check_trades),
    route('btc-cnnbt', check_trades),
    route('btc-eunbt', check_trades),
    route('usd-usnbt', check_trades),
    route('cny-cnnbt', check_trades),
    route('eur-eunbt', check_trades),
]
