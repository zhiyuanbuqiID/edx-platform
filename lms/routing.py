from channels.routing import route

from lms.consumers import ws_message

channel_routing = [
#    route("http.request", "lms.consumers.http_consumer"),

    route('websocket.receive', ws_message)
]
