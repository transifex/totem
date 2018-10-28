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
from temcheck.checks.checks import (
    BranchNameCheck, CommitMessagesCheck, PRTitleCheck, PRBodyExcludesCheck,
    PRBodyIncludesCheck, PRBodyChecklistCheck,
    TYPE_BRANCH_NAME, TYPE_COMMIT_MESSAGE, TYPE_PR_BODY_INCLUDES,
    TYPE_PR_BODY_EXCLUDES, TYPE_PR_TITLE, TYPE_PR_BODY_CHECKLIST,
)


class TemCheck:
    """The main class that knows how to perform a bunch of checks
     but also allows clients to register custom behaviour.
     """

    def __init__(self, config_dict, pr_url):
        """Constructor.

        Creates instances of ContentProviderFactory and CheckFactory and allows
        clients to register new functionality on them. This can be done via:
        >>> check = TemCheck({}, '')
        >>> check.content_provider_factory.register('new_type', MyProviderClass)
        >>> check.check_factory.register('new_type', MyCheckClass)

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
        self._register_defaults()

    def _register_defaults(self):
        """Add the default functionality."""
        defaults = {
            TYPE_BRANCH_NAME: BranchNameCheck,
            TYPE_PR_TITLE: PRTitleCheck,
            TYPE_PR_BODY_CHECKLIST: PRBodyChecklistCheck,
            TYPE_PR_BODY_INCLUDES: PRBodyIncludesCheck,
            TYPE_PR_BODY_EXCLUDES: PRBodyExcludesCheck,
            TYPE_COMMIT_MESSAGE: CommitMessagesCheck,
        }
        for config_type, check_class in defaults.items():
            self.check_factory.register(config_type, check_class)

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
