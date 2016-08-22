from channels import route
from consumers.check_trades import check_trades
from consumers.websockets import ws_connect, ws_receive

channel_routing = [
    # set up web sockets for updating the front end
    route('websocket.connect', ws_connect),
    route('websocket.receive', ws_receive),
    #route('websocket.disconnect', ws_disconnect),

    # set a channel per pair to check for trades as orders are added
    route('btc-usnbt', check_trades),
    route('btc-cnnbt', check_trades),
    route('btc-eunbt', check_trades),
    route('usd-usnbt', check_trades),
    route('cny-cnnbt', check_trades),
    route('eur-eunbt', check_trades),
]
