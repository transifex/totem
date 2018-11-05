"""This is where the check suite is created and executed.

Any client that wants to be an entry point should use this module.
For example, a client could be a CLI.

If more Git services need to be supported in the future, this needs
to be refactored.
"""

from temcheck.checks.checks import (
    TYPE_BRANCH_NAME,
    TYPE_COMMIT_MESSAGE,
    TYPE_PR_BODY_CHECKLIST,
    TYPE_PR_BODY_EXCLUDES,
    TYPE_PR_BODY_INCLUDES,
    TYPE_PR_TITLE,
    BranchNameCheck,
    CommitMessagesCheck,
    PRBodyChecklistCheck,
    PRBodyExcludesCheck,
    PRBodyIncludesCheck,
    PRTitleCheck,
)
from temcheck.checks.config import ConfigFactory
from temcheck.checks.core import CheckFactory
from temcheck.checks.suite import CheckSuite
from temcheck.github.content import ContentProviderFactory, GithubContentProvider
from temcheck.github.utils import parse_pr_url
from temcheck.reporting.reports import ConsoleReport, PRCommentReport


class TemCheck:
    """The main class that knows how to perform a bunch of checks
     but also allows clients to register custom behaviour.
     """

    def __init__(self, config_dict, pr_url, details_url=None):
        """Constructor.

        Creates instances of ContentProviderFactory and CheckFactory and allows
        clients to register new functionality on them. This can be done via:
        >>> check = TemCheck({}, '')
        >>> check.content_provider_factory.register('new_type', MyProviderClass)
        >>> check.check_factory.register('new_type', MyCheckClass)

        :param dict config_dict: the full configuration of the suite
            formatted as follows:
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
        :param str pr_url: the URL of the pull request to check
        :param str details_url: the URL to visit for more details about the results
            e.g. this could be the CI page that ran the check suite
        """
        self._config_dict = config_dict

        self.pr_url = pr_url
        self.details_url = details_url
        self.full_repo_name, self.pr_number = parse_pr_url(pr_url)
        self._content_provider_factory = ContentProviderFactory(
            self.full_repo_name, self.pr_number
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
        config = ConfigFactory.create(self._config_dict)
        print(ConsoleReport.get_pre_run_report(config, self.pr_url))
        suite = CheckSuite(
            config=config,
            content_provider_factory=self.content_provider_factory,
            check_factory=self._check_factory,
        )
        suite.run()
        print(ConsoleReport.get_detailed_results(suite.results))
        print(ConsoleReport.get_summary(suite.results))

        content_provider = GithubContentProvider(
            repo_name=self.full_repo_name, pr_num=self.pr_number
        )

        if config.pr_comment_report.get('enabled', True):
            # Create a comment on the PR with a short summary
            pr_report = PRCommentReport(suite, self.details_url)
            try:
                print(pr_report.get_pre_run())
                comment_dict = content_provider.create_pr_comment(
                    pr_report.get_summary()
                )
            except Exception as e:
                print(pr_report.get_error(e))
            else:
                print(pr_report.get_success(comment_dict))

        return suite.results
