"""This is where the check suite is created and executed.

Any client that wants to be an entry point should use this module.
For example, a client could be a CLI.

If more Git services need to be supported in the future, this needs
to be refactored.
"""

from temcheck.checks.checks import CheckFactory
from temcheck.checks.suite import CheckSuite
from temcheck.github.content import ContentProviderFactory
from temcheck.github.utils import parse_pr_url
from temcheck.reporting.reports import print_detailed_results, print_pre_run


class TemCheck:
    """A global provider of the factory objects needed for the suite to run."""

    def __init__(self, config_dict, pr_url):
        """Constructor.

        :param dict config_dict: the full configuration of the suite
            formatted as described in CheckSuite
        :param str pr_url: the URL of the pull request to check
        """
        self._config_dict = config_dict

        full_repo_name, pr_number = parse_pr_url(pr_url)
        self._content_provider_factory = ContentProviderFactory(
            full_repo_name, pr_number
        )
        self._check_factory = CheckFactory()

    @property
    def content_provider_factory(self):
        return self._content_provider_factory

    @property
    def check_factory(self):
        return self._check_factory

    def run(self):
        """Run all registered checks of the suite.

        :return: the results of the execution of the tests
        :rtype: CheckSuiteResults
        """
        print_pre_run(self._config_dict)
        suite = CheckSuite(
            all_configs=self._config_dict,
            content_provider_factory=self._content_provider_factory,
            check_factory=self._check_factory,
        )
        suite.run()
        print_detailed_results(suite.results)

        return suite.results
