from channels.routing import route

from lms.consumers import ws_message, ws_connect, ws_disconnect

channel_routing = [
#    route("http.request", "lms.consumers.http_consumer"),

    route('websocket.connect', ws_connect),
    route('websocket.receive', ws_message),
    route('websocket.dsiconnect', ws_disconnect),
]
