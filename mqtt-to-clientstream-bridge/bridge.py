from aiohttp import web
from paho.mqtt.client import Client
import daiquiri
from exceptions import ConfigException
logger = daiquiri.getLogger(__name__)

class Bridge(object):
    WEBSOCKETS="websocket"
    SSE="sse"
    def __init__(self, args):
        try:
            self.mqtt_host = args["mqtt-to-server"]["broker"]["host"]
            self.mqtt_port = args["mqtt-to-server"]["broker"]["port"]
            self.stream_protocol = args["server-to-client"]["protocol"]
        except KeyError as e:
            raise ConfigException("Error when accessing field", e) from e

