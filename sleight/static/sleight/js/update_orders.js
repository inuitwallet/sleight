
$(function() {
    // When we're using HTTPS, use WSS too.
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var order_sock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + window.location.pathname);

    order_sock.onmessage = function (message) {
        var data = JSON.parse(message.data);
        // we receive both orders and trades.
        // check the message type to see which we have
        if (data.message_type == 'order') {
            //we have an order
            var order_row = $('#order_' + data.order_id);
            var row_num = 0;
            // Check for an order and update it if it exists
            if (order_row.length) {
                // if the amount is 0 or the order is complete or cancelled, we remove it
                if (data.amount == 0 || data.state == 'complete' || data.state == 'cancelled') {
                    order_row.fadeOut(100).fadeIn(100).fadeOut(100).remove();
                } else {
                    // otherwise we just update the amount on order
                    var amount_field = $('#order_' + data.order_id + '_amount');
                    amount_field.text(data.amount);
                    amount_field.fadeOut(100).fadeIn(100);
                }
            } else {
                // order doesn't exist
                var table_rows = $('#' + data.order_type + '_orders tbody tr');
                var new_row = '<tr id="order_' + data.order_id + '">' +
                    '<td class="id">' + data.order_id + '</td>' +
                    '<td id="order_' + data.order_id + '_price" class="price">' + data.price + '</td>' +
                    '<td id="order_' + data.order_id + '_amount">' + data.amount + '</td>' +
                    '</tr>';
                // sometimes the order table is empty so we should insert the new order at the top
                if (table_rows.length == 0) {
                    $('#' + data.order_type + '_orders tbody').append(new_row);
                    $('#order_' + data.order_id).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
                } else {
                    // loop through the table to figure out where to put the new order
                    var i = 0;
                    var row = 0;
                    var inserted = false;

                    $(table_rows).each(function () {
                        var id = $(this).find('td.id').text();
                        var price = $(this).find('td.price').text();
                        i++;
                        row = i - 1;
                        if ((data.order_type == 'ask' && price > data.price) || (data.order_type == 'bid' && price < data.price)) {
                            table_rows.eq(row).before(new_row);
                            $('#order_' + data.order_id).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
                            inserted = true;
                            return false;
                        }
                    });
                    if (inserted == false) {
                        $('#' + data.order_type + '_orders tbody').append(new_row);
                        $('#order_' + data.order_id).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
                    }
                }
            }
        }

        if (data.message_type == 'trade') {
            //we have a trade
            console.log(data);
            //build the new row and put it at the top of the trade table
            var new_trade_row = '<tr id="trade_' + data.trade_id + '">' +
                              '<td>' + data.trade_time + '</td>' +
                              '<td>' + data.trade_type + '</td>' +
                              '<td>' + data.price+ '</td>' +
                              '<td>' + data.amount + '</td>' +
                              '<td>' + data.initiating_id + '</td>' +
                              '<td>' + data.existing_id + '</td>' +
                          '</tr>';
            $('#trades > tbody > tr:first').before(new_trade_row);
            $('#trade_' + data.trade_id).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
        }
    };
});
