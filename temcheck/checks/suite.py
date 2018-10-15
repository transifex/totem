from temcheck.checks.checks import CheckFactory
from temcheck.checks.config import CheckConfig, FAILURE_LEVEL_ERROR
from temcheck.checks.results import (
    CheckResult, CheckSuiteResults, STATUS_ERROR, ERROR_GENERIC
)


class CheckSuite:
    """Executes all checks and creates a report.

    This is a stateful class that keeps track of how each check went.
    It is the class that handles all the checks. All it requires is
    a configuration (what checks to perform and with what parameters)
    and it handles everything else.

    In order to use it, you just need to create an instance with
    all necessary configuration and then call `run()`.
    All checks run synchronously.
    """

    def __init__(self, all_configs, content_provider_factory):
        """Constructor.

        :param dict all_configs: a dictionary that contains the configuration for
            all checks, formatted like:
            {
              'branch_name': {
                'pattern': '^TX-[0-9]+\-[\w\d\-]+$',
                'failure_level': 'warning'
              },
              'pr_description_checkboxes': {
                'failure_level': 'error',
              },
              'commit_message': {
                'title_max_length': 52,
                'body_max_length': 70,
                'failure_level': 'error',
              }
            }
        :param BaseContentProviderFactory content_provider_factory: an object that
            knows how to create content providers for a specific Git service
        """
        self.content_provider_factory = content_provider_factory
        self.configs = {}

        # Convert the configuration dictionary into CheckConfig objects
        # and store them in memory
        for check_type, config_dict in all_configs.items():
            config = self._create_config(check_type, config_dict)
            self.configs[check_type] = config

        self.results = CheckSuiteResults()

    def run(self):
        """Execute all checks that the suite contains and store the results.

        Checks are executed synchronously, one by one.
        This is the main point of the application where the actual magic happens.
        """
        # For every configuration object a proper content provider
        # is created and then given to a check object that knows
        # what to test. Each result is added to the suite.
        # along with a content provider and these are fed to
        for config in self.configs.values():
            check = CheckFactory.create(config)

            try:
                content = self.content_provider_factory.create(check).get_content()
                result = check.run(content)
            except Exception as e:
                result = CheckResult(
                    config, STATUS_ERROR, ERROR_GENERIC, message=str(e)
                )

            self.results.add(result)

    def _create_config(self, check_type, config_dict):
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
