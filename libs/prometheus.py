"""
Prometheus client side logic.
"""
# pylint: disable=too-few-public-methods
import sys
from loguru import logger
from prometheus_client import start_http_server


class PrometheusClient:
    """
    Prometheus http server initialization.
    """

    def __init__(self, config, dependency):
        self.config = config
        self.dependency = dependency
        start_http_server(
            port=self.config["config"]["main"]["exporterPort"],
            addr=config["config"]["main"]["exporterAddress"],
        )
        logger.info(
            f'Exposing metrics on http://{config["config"]["main"]["exporterAddress"]}:'
            f'{self.config["config"]["main"]["exporterPort"]}'
        )

    def start_client(self):
        """
        A dummy method for thread loop.

        :return:
        """
        while True:
            if self.dependency.is_alive():
                pass
            else:
                logger.error(
                    f"Dependent {self.dependency.name} thread is down, exited."
                )
                sys.exit(1)
