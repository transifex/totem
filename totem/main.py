"""This is where the check suite is created and executed.

Any client that wants to be an entry point should use this module.
For example, a client could be a CLI.

If more Git services need to be supported in the future (other than Github),
this needs to be refactored.
"""

from totem.checks.checks import (
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
from totem.checks.config import ConfigFactory
from totem.checks.content import BaseContentProvider, BaseGitContentProviderFactory
from totem.checks.core import CheckFactory
from totem.checks.results import CheckSuiteResults
from totem.checks.suite import CheckSuite
from totem.git.content import GitContentProviderFactory, PreCommitContentProviderFactory
from totem.github.content import GithubContentProviderFactory, GithubPRContentProvider
from totem.github.utils import parse_pr_url
from totem.reporting.console import Color, LocalConsoleReport, PRConsoleReport
from totem.reporting.pr import PRCommentReport


class BaseCheck:
    """This is the base class that performs a bunch of checks.

    Provides basic convenience functionality that subclasses
    can use. Subclasses need to override `run()`.
    """

    def __init__(self):
        self._check_factory: CheckFactory = CheckFactory()
        self._register_defaults()
        self._content_provider_factory: BaseGitContentProviderFactory = None

    def run(self) -> CheckSuiteResults:
        """Run all checks.

        Subclasses need to do the following:
         1. Create a `Config` object, using `ConfigFactory.create()`
         2. Create a suite, using `suite = self._create_suite(config)`
         3. Run the suite, using `suite.run()`
         4. Return the results, via `return suite.results`

        :return: the results of the execution of the tests
        :rtype: CheckSuiteResults
        """
        raise NotImplementedError()

    @property
    def check_factory(self) -> CheckFactory:
        return self._check_factory

    @property
    def content_provider_factory(self) -> BaseGitContentProviderFactory:
        return self._content_provider_factory

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

    def _create_suite(self, config) -> CheckSuite:
        """Create a check suite to run all checks defined in the
        given config.

        :param Config config: the full configuration of all checks
        :return: the suite that will run all checks
        :rtype: CheckSuite
        """
        return CheckSuite(
            config=config,
            content_provider_factory=self._content_provider_factory,
            check_factory=self._check_factory,
        )


class PRCheck(BaseCheck):
    """The main class that knows how to perform a bunch of checks
    on a pull request.

    Also allows clients to register custom behaviour.
    """

    def __init__(self, config_dict: dict, pr_url: str, details_url: str = None):
        """Constructor.

        Creates instances of ContentProviderFactory and CheckFactory and allows
        clients to register new functionality on them. This can be done via:
        >>> check = PRCheck({}, '')
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
        super().__init__()
        self._config_dict = config_dict

        self.pr_url = pr_url
        self.details_url = details_url
        try:
            self.full_repo_name, self.pr_number = parse_pr_url(pr_url)
        except IndexError:
            print(
                Color.format(
                    '[error]PR URL cannot be parsed, '
                    'seems invalid: "{}"[end]'.format(pr_url)
                )
            )
            raise
        self._content_provider_factory = GithubContentProviderFactory(
            self.full_repo_name, self.pr_number
        )

    def run(self) -> CheckSuiteResults:
        """Run all registered checks of the suite.

        :return: the results of the execution of the tests
        :rtype: CheckSuiteResults
        """
        config = ConfigFactory.create(self._config_dict, include_pr=True)
        suite = self._create_suite(config)

        report = PRConsoleReport(suite)
        print(report.get_pre_run_report(config, self.pr_url))

        suite.run()
        print(report.get_detailed_results(suite.results))
        print(report.get_summary(suite.results))

        content_provider = GithubPRContentProvider(
            repo_name=self.full_repo_name, pr_num=self.pr_number
        )

        # See if we need to add a PR comment report
        if config.pr_comment_report.get('enabled', True):
            # Attempt to create the comment. If it fails, `results` will be None
            results = self._create_pr_comment_report(suite, content_provider)

            # See if we need to delete previous PR comments
            # Do NOT do that if the new comment failed to be created
            delete_previous = config.pr_comment_report.get('delete_previous', False)
            if results is not None and delete_previous:
                self._delete_previous_pr_comment(suite, results['id'], content_provider)

        return suite.results

    def _create_pr_comment_report(
        self, suite: CheckSuite, content_provider: BaseContentProvider
    ) -> dict:
        """Create a comment on the PR with a short summary of the results.

        :param CheckSuite suite: the suite that was executed
        :param BaseContentProvider content_provider: the object that has
            the ability to create a PR comment
        :return: information about the created comment
        :rtype: dict
        """
        pr_report = PRCommentReport(suite, self.details_url)
        console_report = PRConsoleReport(suite)
        try:
            print(console_report.PRComments.get_creation_pre_run())
            comment_dict = content_provider.create_pr_comment(pr_report.get_summary())
            print(console_report.PRComments.get_creation_success(comment_dict))
            return comment_dict

        except Exception as e:
            print(PRConsoleReport.PRComments.get_creation_error(e))
            return {}

    def _delete_previous_pr_comment(
        self, suite: CheckSuite, comment_id: int, content_provider: BaseContentProvider
    ) -> bool:
        """Delete the previous totem comment of the PR.

        Useful if the comments stack up and create clutter, in which case
        only the last comment will be kept.

        :param CheckSuite suite: the suite that was executed
        :param int comment_id: the ID of the comment to leave intact
        :param BaseContentProvider content_provider: the object that has
            the ability to delete PR comments
        :return: True if the previous comment was deleted, False otherwise
        :rtype: bool
        """
        console_report = PRConsoleReport(suite)
        try:
            print()
            print(console_report.PRComments.get_deletion_pre_run())
            success = content_provider.delete_previous_pr_comment(comment_id)
            if success:
                print(console_report.PRComments.get_deletion_success())
            else:
                print(console_report.PRComments.get_deletion_failure())

            return success

        except Exception as e:
            print(console_report.PRComments.get_deletion_error(e))
            return False


class LocalCheck(BaseCheck):
    """The main class that knows how to perform a bunch of checks
    on a local Git branch.


    Also allows clients to register custom behaviour.
    """

    def __init__(self, config_dict: dict):
        """Constructor.

        Creates instances of ContentProviderFactory and CheckFactory and allows
        clients to register new functionality on them. This can be done via:
        >>> check = LocalCheck(config_dict)
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
        """
        super().__init__()
        self._config_dict = config_dict
        self._content_provider_factory = GitContentProviderFactory()

    def run(self) -> CheckSuiteResults:
        """Run all registered checks of the suite.

        :return: the results of the execution of the tests
        :rtype: CheckSuiteResults
        """
        config = ConfigFactory.create(self._config_dict, include_pr=False)
        suite = self._create_suite(config)
        suite.run()

        report = LocalConsoleReport(suite)
        print(report.get_detailed_results(suite.results))

        return suite.results


class PreCommitLocalCheck(BaseCheck):
    """Knows how to perform a bunch of checks just before a local commit
    takes place.

    Also allows clients to register custom behaviour.
    """

    def __init__(self, config_dict: dict):
        """Constructor.

        Creates instances of ContentProviderFactory and CheckFactory and allows
        clients to register new functionality on them. This can be done via:
        >>> check = PreCommitLocalCheck(config_dict)
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
        """
        super().__init__()
        self._config_dict = config_dict
        self._content_provider_factory = PreCommitContentProviderFactory()

    def run(self) -> CheckSuiteResults:
        """Run all registered checks of the suite.

        :return: the results of the execution of the tests
        :rtype: CheckSuiteResults
        """
        config = ConfigFactory.create(self._config_dict, include_pr=False)
        suite = self._create_suite(config)
        suite.run()

        report = LocalConsoleReport(suite)
        show_warnings = report.report_details.get('show_warnings', True)
        if suite.results.errors or (show_warnings and suite.results.warnings):
            print(report.get_detailed_results(suite.results))

        return suite.results
