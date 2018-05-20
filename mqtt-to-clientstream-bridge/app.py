from aiohttp import web
import yaml
import logging
import daiquiri
from pathlib import Path
import argparse
from bridge import Bridge
from exceptions import ConfigException
daiquiri.setup(level=logging.INFO)

logger = daiquiri.getLogger(__name__)

def parse_config(config_path):
    logger.info("Using Config: %s" % config_path)
    try:
        with open(config_path, 'r') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as e:
                raise ConfigException("Error when parsing config", e)
    except FileNotFoundError as e:
        raise ConfigException("Configfile not found", e) from e


def main():
    logger.info("initializing bridge")
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Configuration file')
    args = parser.parse_args()
    config = parse_config(Path(args.config).resolve())
    bridge = Bridge(config)



if __name__ == "__main__":
    main()
