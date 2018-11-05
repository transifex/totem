
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

    def __init__(self, check_type, failure_level, **options):
        """
        Constructor.

        `options` must be a dictionary with all necessary parameters for each check.
        Each check can have different parameters.

        :param str check_type: a unique string that shows what type of check
            this is
        :param str failure_level: defines how a failed check should be treated
            (an error would block merging, whereas a warning would not)
        :param dict options: a dictionary with all configuration options
        """
        self.check_type = check_type
        self.failure_level = failure_level
        self.options = options


class Config:
    """Represents the whole configuration of the library.

    Determines what checks will run and with which parameters, as well as
    other parts of the behaviour of this tool.
    """

    def __init__(self, settings, check_configs):
        """Constructor.

        :param dict settings: a dictionary with all generic settings,
            containing a dict for each type of setting
        :param dict check_configs: a dictionary with the configuration for
            the checks, with the check type as the key and a CheckConfig object
            as the value
        """
        self._settings = settings
        self._check_configs = check_configs

    @property
    def settings(self):
        """The generic settings of the tool.

        :return: a dictionary with all generic settings, containing a dict
            for each type of setting
        :rtype: dict
        """
        return self._settings

    @property
    def pr_comment_report(self):
        """The configuration of the PR comment report feature.

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
    def check_configs(self):
        """A dictionary with the configuration for all checks.

        :return: a dictionary with CheckConfig objects as values
        :rtype: dict
        """
        return self._check_configs


class ConfigFactory:
    """Responsible for creating the Config object that represents the
    configuration for the whole library."""

    @staticmethod
    def create(config_dict):
        """Create a new Config object.

        :param dict config_dict: a dictionary with the full configuration
            of all available settings
        :return: the new config
        :rtype: Config
        """
        settings = config_dict.get('settings', {})
        checks = config_dict.get('checks', {})

        check_configs = {}
        for check_type, config_dict in checks.items():
            config = ConfigFactory._create_check_config(check_type, config_dict)
            check_configs[check_type] = config

        return Config(settings, check_configs)

    @staticmethod
    def _create_check_config(check_type, config_dict):
        """Create a CheckConfig object with the given type and parameters.

        :param str check_type: a string that shows what type of check
            this config is about
        :param dict config_dict: all configuration options
        :return: the config object
        :rtype: CheckConfig
        """
        config = dict(config_dict)
        failure_level = config.pop('failure_level', FAILURE_LEVEL_ERROR)

        return CheckConfig(check_type=check_type, failure_level=failure_level, **config)
