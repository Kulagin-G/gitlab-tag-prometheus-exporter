"""
Shared functions.
"""
import sys
from concurrent.futures import ThreadPoolExecutor

import yaml
import semver
from loguru import logger


def load_yaml_file(file_path: str) -> yaml.YAMLObject:
    """
    Load YAML file as an YAMLObject.

    file_path: string of the full file path.
    """
    try:
        with open(file=f"{file_path}", mode="r", encoding="utf-8") as file_dump:
            return yaml.safe_load(file_dump)
    except FileNotFoundError:
        logger.error(f"Config file not found: {file_path}")
        sys.exit(1)


# pylint: disable=invalid-name
def do(function, **kwargs) -> list:
    """
    Concurrency request wrapper.

    :param function: function object.
    :param kwargs: iterator to iterate on.
    :return: <list>
    """
    results = []
    kwargs["add_meta"] = (
        False if not kwargs.get("add_meta", False) else kwargs["add_meta"]
    )
    kwargs["workers"] = 20 if not kwargs.get("workers", []) else kwargs["workers"]
    with ThreadPoolExecutor(max_workers=kwargs["workers"]) as executor:
        futures = [
            executor.submit(function, i, kwargs["add_meta"]) for i in kwargs["iterator"]
        ]
        for future in futures:
            try:
                results.append(future.result(timeout=90))
            # pylint: disable=invalid-name,broad-except
            except Exception as e:
                results.append(None)
                logger.warning(e)
    return results


def is_semver(tag: str) -> bool:
    """
    Check whether provided tag is compatible with semver.

    :param tag: tag name to parse with semver.
    :return: bool
    """
    logger.debug(f"Is {tag} tag semver?")
    try:
        semver.parse_version_info(tag)
        logger.debug(f"{tag} tag is semver-compatible type.")
        return True
    except ValueError:
        return False
