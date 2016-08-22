
$(function() {
    // When we're using HTTPS, use WSS too.
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var order_sock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + window.location.pathname);

    order_sock.onmessage = function (message) {
        console.log(message.data);
        alert(message.data);
    };

});
