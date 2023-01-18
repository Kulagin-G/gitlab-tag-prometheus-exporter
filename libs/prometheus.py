"""
Prometheus client side logic.
"""
# pylint: disable=too-few-public-methods
from loguru import logger
from prometheus_client import start_http_server


class PrometheusClient:
    """
    Prometheus http server initialization.
    """

    def __init__(self, config):
        self.config = config
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
            pass
