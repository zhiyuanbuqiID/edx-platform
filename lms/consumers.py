import json

from django.http import HttpResponse
from channels.handler import AsgiHandler
from channels.sessions import channel_session
from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http

from courseware.module_render import xblock_view_msg

def http_consumer(message):
    # Make standard HTTP response - access ASGI path attribute directly
    response = HttpResponse("Hello world! You asked for %s" % message.content['path'])
    # Encode that response into message format (ASGI)
    for chunk in AsgiHandler.encode_response(response):
        message.reply_channel.send(chunk)

@http_session_user
def ws_message(message):
    # ASGI WebSocket packet-received and send-packet message types
    # both have a "text" key for their textual data.
    usage_ids = json.loads(message.content['text'])

    print dir(message)
    print message

    # Step #1: Do it all here.
    for usage_id in usage_ids:
        xblock_view_msg(message, usage_id)
