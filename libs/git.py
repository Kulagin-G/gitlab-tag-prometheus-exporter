"""
Git parser and metrics generator.
"""
# pylint: disable=invalid-name,no-else-return
import copy
import re
import os

import gitlab
from loguru import logger

from requests.exceptions import ConnectionError as reqConnectionError
from gitlab.v4.objects import (
    Project,
)
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError

from prometheus_client import Info
from prometheus_client.metrics import MetricWrapperBase

from .common import do, is_semver


def semver_tags(tags: list, pattern: str) -> list:
    """
    Parse semver tags by the pattern and return the latest one.

    :return: list
    """

    for element in tags:
        latest_valid_tags = [
            t.name
            for t in element["semver_tags"]
            if re.match(pattern=rf"{pattern}", string=t.name)
        ]
        element["semver_tags"] = latest_valid_tags[0] if latest_valid_tags else None

    return tags


class GitParser:
    """
    Git parser class - any interaction with GitLab should be invoked from here.
    """

    def __init__(self, config):
        self.config = config
        self.gl = self.__gitlab_init()  # pylint: disable=invalid-name
        self.health = self.is_healthy()
        if self.health:
            self.managed_projects = self.__gitlab_projects_init()

    def __gitlab_init(self) -> gitlab.Gitlab | None:
        """
        Private method to define Gitlab associated Python object.

        :return: gitlab.Gitlab
        """
        gitlab_url, gitlab_api_token = self.config["config"]["main"][
            "gitlabUrl"
        ], os.getenv("GITLAB_API_TOKEN", None)
        logger.info("Gitlab initialization.")
        return gitlab.Gitlab(url=gitlab_url, private_token=gitlab_api_token)

    def is_healthy(self) -> bool:
        """
        Show authentication works correctly.

        :return:
        """
        try:
            self.gl.auth()
            logger.info("Gitlab connection is healthy.")
            return True
        except GitlabAuthenticationError as e:
            logger.error(f"Check Gitlab API credentials: {e}")
            logger.error("Gitlab connection is not healthy.")
            return False
        except reqConnectionError as e:
            logger.error(f"Check hostname or network connection: {e}")
            logger.error("Gitlab connection is not healthy.")
            return False

    def __gitlab_projects_init(self) -> list:
        """
        Load managed Gitlab projects as a list of RestAPI objects.
        :return: list
        """
        if self.config["config"]["gitProjects"]:
            return do(
                function=self.__get_project,
                iterator=self.config["config"]["gitProjects"],
                add_meta=False,
            )
        else:
            logger.warning("git-projects are not set in the config!")
            return []

    def __get_project(self, project_config: dict, add_meta: bool) -> Project | None:
        """
        Private method to initiate Gitlab project associated Python object.

        :param project_config: distribution-projects element.
        :return: gitlab.v4.objects.Project
        """
        _ = add_meta

        try:
            logger.info(f"Loading {project_config['name']} project.")
            return self.gl.projects.get(project_config["gitProjectPath"])
        except GitlabGetError as e:  # pylint: disable=invalid-name
            logger.error(f'{project_config["gitProjectPath"]} not found: {e}')
            return None

    def __fetch_project_tags(self, project: Project, add_meta: bool) -> list | dict:
        """
        Fetch all project tags concurrently.

        :param project: target Gitlab project.
        :param add_meta: add metadata into output.
        :return: list | dict
        """
        if add_meta:
            return {
                "project_name": project.name,
                "repository": project.ssh_url_to_repo,
                "tags": project.tags.list(all=True),
            }
        else:
            return project.tags.list(all=True)

    def latest_semver_tags(self) -> tuple:
        """
        Fetch the latest semver tag from managed Gitlab project.

        :return: tuple
        """
        logger.info("Loading Gitlab projects tags.")
        valid_tags = []
        project_tags = do(
            function=self.__fetch_project_tags,
            iterator=self.managed_projects,
            add_meta=True,
        )
        logger.debug(f"All available tags: {project_tags}")
        for element in project_tags:
            try:
                project = {
                    "project_name": element["project_name"],
                    "repository": element["repository"],
                    "semver_tags": [],
                }
            except TypeError:
                logger.error("GitlabAPI returned an error, see logs above!")
                project = {
                    "project_name": "GitlabApiError",
                    "repository": "GitlabApiError",
                    "semver_tags": [],
                }
            for tag in element["tags"]:
                if is_semver(tag=tag.name):
                    project["semver_tags"].append(tag)
            valid_tags.append(project)

        valid_rc_tags = copy.deepcopy(valid_tags)
        valid_rel_tags = copy.deepcopy(valid_tags)

        return semver_tags(
            tags=valid_rc_tags,
            pattern=self.config["config"]["main"]["releaseCandidateTagPattern"],
        ), semver_tags(
            tags=valid_rel_tags,
            pattern=self.config["config"]["main"]["releaseTagPattern"],
        )


class GitMetricGenerator(GitParser):
    """
    Metrics generator class.

    """

    def __init__(self, config):
        self.rc_tag_metric = Info(
            "gitlab_project_rc_tag_info",
            "The latest release-candidate tag from project.",
            ["project_name", "repository", "tag_version"],
        )
        self.rel_tag_metric = Info(
            "gitlab_project_rel_tag_info",
            "The latest release tag project.",
            ["project_name","repository",  "tag_version"],
        )
        logger.debug(f"GitMetricGenerator class initialization: {self.__dict__}")
        super().__init__(config=config)

    def _remove_redundant_metric(self, metric: MetricWrapperBase):
        """
        Remove old metrics if they are.

        :param metric: MetricWrapperBase object.
        :return:
        """
        metrics_data = metric.collect()
        if metrics_data[0].samples:
            logger.debug(f"Clearing out metrics data: {metrics_data[0].samples}")
            metric.clear()

    def metric_gitlab_rc_tag_info(self, data: list):
        """
        Update metric labels.

        :param data: data for labels.
        :return:
        """
        logger.info(f"Updating {self.rc_tag_metric} metrics group.")
        self._remove_redundant_metric(metric=self.rc_tag_metric)
        for element in data:
            logger.debug(
                f'Updating data: {element["project_name"]}: {element["semver_tags"]}'
            )
            self.rc_tag_metric.labels(
                element["project_name"], element["repository"], element["semver_tags"]
            )

    def metric_gitlab_rel_tag_info(self, data: list):
        """
        Update metric labels.

        :param data: data for labels.
        :return:
        """
        logger.info(f"Updating {self.rel_tag_metric} metrics group.")
        self._remove_redundant_metric(metric=self.rel_tag_metric)
        for element in data:
            logger.debug(
                f'Updating data: {element["project_name"]}: {element["semver_tags"]}'
            )
            self.rel_tag_metric.labels(
                element["project_name"], element["repository"], element["semver_tags"]
            )

    def generate_metrics(self, **kwargs: list):
        """
        A common wrapper for metric generation.

        :param kwargs: keyworded variable-length argument list.
        :return:
        """
        self.metric_gitlab_rc_tag_info(data=kwargs["rc_tags"])
        self.metric_gitlab_rel_tag_info(data=kwargs["rel_tags"])
        logger.info("Metrics generation is done!")
        logger.info(
            f"GitMetricGenerator thread is waiting for "
            f"{self.config['config']['main']['pollingTimeoutSec']}s timeout."
        )
