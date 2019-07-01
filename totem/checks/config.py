from typing import List

FAILURE_LEVEL_WARNING = 'warning'
FAILURE_LEVEL_ERROR = 'error'


class CheckConfig:
    """Represents the configuration of a single check.

    A single check can be something like the format of a branch name.

    The config class is agnostic to specific checks; it keeps the configuration
    in a generic dictionary. It is up to the consumer of this class to know
    what type of information to retrieve, based on the ID (key) of the config.

    For example, a class that wants to check if a branch name has a certain prefix
    should know the proper keys to look for in the config object (in this case
    the branch name and the expected prefix).
    """

    def __init__(self, check_type: str, failure_level: str, **options):
        """
        Constructor.

        `options` must be a dictionary with all necessary parameters for each check.
        Each check can have different parameters.

        :param str check_type: a unique string that shows what type of check
            this is
        :param str failure_level: defines how a failed check should be treated
            (an error would block merging, whereas a warning would not)
        """
        self.check_type = check_type
        self.failure_level = failure_level
        self.options = options


class Config:
    """Represents the whole configuration of the library.

    Determines what checks will run and with which parameters, as well as
    other parts of the behaviour of this tool.
    """

    def __init__(self, settings: dict, check_configs: List[CheckConfig]):
        """Constructor.

        :param dict settings: a dictionary with all generic settings,
            containing a dict for each type of setting
        :param List[CheckConfig] check_configs: a list of CheckConfig objects
        """
        self._settings = settings
        self._check_configs = check_configs

    @property
    def settings(self) -> dict:
        """The generic settings of the tool.

        :return: a dictionary with all generic settings, containing a dict
            for each type of setting
        :rtype: dict
        """
        return self._settings

    @property
    def check_config_types(self) -> List[str]:
        """A list of all the unique check types that appear in this configuration."""
        return list({x.check_type for x in self.check_configs})

    @property
    def check_configs(self) -> List[CheckConfig]:
        """Contains all the configuration for the checks,
        with the check type as the key and a CheckConfig object
        as the value

        :return: the configurations for all checks
        :rtype: List[CheckConfig]
        """
        return self._check_configs

    @property
    def pr_comment_report(self) -> dict:
        """The configuration of the PR comment report feature.

        Determines what information will be shared on a comment
        on a pull request.

        :return: a dictionary with the existing config options, or the fallback
            default options if none defined
        :rtype: dict
        """
        return self.settings.get(
            'pr_comment_report',
            {
                'enabled': True,
                'show_message': True,
                'show_empty_sections': False,
                'show_errors': False,
            },
        )

    @property
    def pr_console_report(self) -> dict:
        """The configuration of the console report feature.

        Determines what information will be shared on a report on the console
        when running on a PR.

        :return: a dictionary with the existing config options, or the fallback
            default options if none defined
        :rtype: dict
        """
        return self.settings.get(
            'console_report',
            {
                'show_empty_sections': True,
                'show_message': True,
                'show_details': True,
                'show_successful': True,
            },
        )

    @property
    def local_console_report(self) -> dict:
        """The configuration of the local console report feature.

        Determines what information will be shared on a report on the console
        when running locally (not on a PR).

        :return: a dictionary with the existing config options, or the fallback
            default options if none defined
        :rtype: dict
        """
        return self.settings.get(
            'local_console_report',
            {
                'show_empty_sections': False,
                'show_message': True,
                'show_details': True,
                'show_successful': False,
            },
        )


class ConfigFactory:
    """Responsible for creating the Config object that represents the
    configuration for the whole library."""

    @staticmethod
    def create(config_dict: dict, include_pr: bool = True) -> Config:
        """Create a new Config object.

        :param dict config_dict: a dictionary with the full configuration
            of all available settings
        :param bool include_pr: if False, all checks that can only
            be applied on PRs will not be included in the config
        :return: the new config
        :rtype: Config
        """
        settings = config_dict.get('settings', {})
        checks = config_dict.get('checks', {})

        from totem.checks.checks import PR_TYPES_CHECKS

        check_configs = []

        if isinstance(checks, dict):
            for check_type, config_dict in checks.items():
                # If `include_pr` is True (e.g. when running on a local repo),
                # exclude all PR-only checks
                if not include_pr and check_type in PR_TYPES_CHECKS:
                    continue

                config_dict['type'] = check_type
                config = ConfigFactory._create_check_config(config_dict)
                check_configs.append(config)

        elif isinstance(checks, list):
            for config_dict in checks:
                # If `include_pr` is True (e.g. when running on a local repo),
                # exclude all PR-only checks
                if not include_pr and config_dict['type'] in PR_TYPES_CHECKS:
                    continue
                config = ConfigFactory._create_check_config(config_dict)
                check_configs.append(config)

        return Config(settings, check_configs)

    @staticmethod
    def _create_check_config(config_dict: dict) -> CheckConfig:
        """Create a CheckConfig object with the given type and parameters.

        :param dict config_dict: all configuration options
        :return: the config object
        :rtype: CheckConfig
        """
        config = dict(config_dict)
        check_type = config.pop('type')
        failure_level = config.pop('failure_level', FAILURE_LEVEL_ERROR)

        return CheckConfig(check_type=check_type, failure_level=failure_level, **config)
