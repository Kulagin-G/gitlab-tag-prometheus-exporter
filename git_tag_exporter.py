#!/usr/bin/env python3
"""
Main exporter entrypoint.
"""
# pylint: disable=invalid-name

import sys
from pprint import pformat
from threading import Thread, Event
import argparse
from art import tprint

from loguru import logger
from yaml import YAMLObject
from libs.defaults import DEFAULTS
from libs.prometheus import PrometheusClient
from libs.git import GitMetricGenerator
from libs.common import load_yaml_file


def start_prometheus_client(config: YAMLObject):
    """
    Func object for individual Thread.

    :param config: YAMLObject
    :return:
    """
    pc = PrometheusClient(config=config)
    pc.start_client()


def start_git_metrics(gms: GitMetricGenerator, timeout: int):
    """
    Func object for individual Thread.

    :param timeout: metric generation timeout.
    :param gms: GitMetricGenerator object.
    :return:
    """
    git_event = Event()
    while True:
        latest_rc_tag, latest_rel_tag = gms.latest_semver_tags()
        logger.info(f"The latest rc projects tags: {latest_rc_tag}")
        logger.info(f"The latest rel projects tags: {latest_rel_tag}")
        gms.generate_metrics(rc_tags=latest_rc_tag, rel_tags=latest_rel_tag)
        git_event.wait(timeout=timeout)


def main():
    """
    The main entrypoint.

    :return: None
    """
    tprint("git exporter")
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-c",
        "--config-path",
        type=str,
        default="./config/config.yaml",
        help="Path to the config file.",
    )

    args = parser.parse_args()
    config = load_yaml_file(file_path=args.config_path)

    log_level = config["config"]["main"]["logLevel"].upper()
    logger.configure(handlers=[DEFAULTS.get("LOGURU_CONFIG")[log_level]])
    logger.debug(f"Provided arguments: \n {pformat(args.__dict__)}")
    logger.debug(f"Loaded defaults: \n {pformat(DEFAULTS)}")
    logger.info(f"Config file path: {args.config_path}")

    gms = GitMetricGenerator(config=config)

    if gms.health:
        prometheus_client: Thread = Thread(
            target=start_prometheus_client, args=(config,)
        )
        prometheus_client.start()
        logger.info(
            f"PrometheusClient thread has been started: {prometheus_client.native_id}"
        )

        git_metrics: Thread = Thread(
            target=start_git_metrics,
            daemon=True,
            args=(gms, config["config"]["main"]["pollingTimeoutSec"]),
        )
        git_metrics.start()
        logger.info(
            f"GitMetricGenerator thread has been started: {git_metrics.native_id}"
        )

        prometheus_client.join()
    else:
        logger.error("Gitlab thread initialization failure!")
        sys.exit(1)


if __name__ == "__main__":
    main()
