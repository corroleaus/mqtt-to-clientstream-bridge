from tornado import ioloop, gen
import yaml
import logging
import daiquiri
import signal
import time
import sys
from pathlib import Path
import argparse
from mqtt_to_clientstream.bridge import Bridge
from mqtt_to_clientstream.exceptions import ConfigException
daiquiri.setup(level=logging.INFO)

logger = daiquiri.getLogger(__name__)


class App(object):
    """ main application
    """

    def __init__(self, config_path, args, dynamic_subscriptions):
        if config_path:
            self.config = self.parse_config(Path(config_path).resolve())
        else:
            self.config = args
        self.dynamic_subscriptions = dynamic_subscriptions
        self.ioloop = ioloop.IOLoop.current()
        self.bridge = Bridge(self.config, self.ioloop,
                             self.dynamic_subscriptions)
        signal.signal(signal.SIGINT, self.sig_handler)

    def start(self):
        """ Start the bridge
        """
        self.bridge.get_app().listen(self.bridge.get_port())
        logger.info("bridge listening on %s" % self.bridge.get_port())
        self.ioloop.start()

    def parse_config(self, config_path):
        """ Parse application config file
        """
        logger.info("Using Config: %s" % config_path)
        try:
            with open(config_path, 'r') as stream:
                try:
                    return yaml.load(stream)
                except yaml.YAMLError as e:
                    raise ConfigException("Error when parsing config", e)
        except FileNotFoundError as e:
            raise ConfigException("Configfile not found", e) from e

    async def shutdown(self):
        """ Cleanup MQTT client and ioloop.
        """
        logger.info('Disconnecting from broker.')
        self.ioloop.add_callback(self.bridge.mqtt_disconnect)
        await gen.sleep(2)
        logger.info('Stopping ioloop.')
        self.ioloop.stop()
        self.ioloop.close()
        self.bridge.get_app().stop()
        sys.exit(0)

    def sig_handler(self, sig, frame):
        """ Basic Signal Handler
        """
        logger.debug('Caught signal: %s', sig)
        logger.info("Exiting gracefully...")
        self.ioloop.add_callback_from_signal(self.shutdown)


def main():
    """ Parse args and initialize app
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='Configuration file')
    parser.add_argument('-b', '--broker-host',
                        help='Broker Host')
    parser.add_argument('-i', '--broker-port', type=int,
                        help='Mqtt broker port')
    parser.add_argument('-p', '--bridge-port', type=int,
                        help='Listening port of the Bridge server')
    parser.add_argument('-s', '--protocol', choices=["websocket", "sse"],
                        help='Protocol -- websocket or sse')
    parser.add_argument('-d', '--dynamic-subscriptions', action='store_true',
                        help='If Dynamic subscriptions is set, the application will subscribe to topics dynamically based on http requests. If a config file is used, the topics list may be omitted.')
    parser.add_argument('-l', '--log-level', required=False, choices=[
                        'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], help='Log Level')
    cli_args = parser.parse_args()
    args = None
    if cli_args.log_level:
        daiquiri.setup(level=getattr(logging, cli_args.log_level))
    if not cli_args.config and (not cli_args.broker_host or not cli_args.broker_port or not cli_args.bridge_port or not cli_args.protocol):
        parser.error(
            "If no configfile is provided: broker host, broker port, bridge port and protocol must be provided.")
    elif not cli_args.config:
        if cli_args.dynamic_subscriptions:
            parser._print_message(
                "Note: Subscriptions are always dynamic when configuration file is omitted.\n")
        else:
            cli_args.dynamic_subscriptions = True
        args = {"server-to-client": {"protocol": cli_args.protocol, "port": cli_args.bridge_port},
                "mqtt-to-server": {"broker": {"host": cli_args.broker_host, "port": cli_args.broker_port}}}
    logger.info("initializing...")
    app = App(cli_args.config, args, cli_args.dynamic_subscriptions)
    app.start()


if __name__ == "__main__":
    main()
