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
from temcheck.github.content import ContentProviderFactory, PRContentProvider
from temcheck.github.utils import parse_pr_url
from temcheck.reporting.console import ConsoleReport
from temcheck.reporting.pr import PRCommentReport


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

        content_provider = PRContentProvider(
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
                self._delete_previous_pr_comment(results['id'], content_provider)

        return suite.results

    def _create_pr_comment_report(self, suite, content_provider):
        """Create a comment on the PR with a short summary of the results.

        :param CheckSuite suite: the suite that was executed
        :param BaseContentProvider content_provider: the object that has
            the ability to create a PR comment
        :return: information about the created comment
        :rtype: dict
        """
        pr_report = PRCommentReport(suite, self.details_url)
        try:
            print(ConsoleReport.PRComments.get_creation_pre_run())
            comment_dict = content_provider.create_pr_comment(pr_report.get_summary())
            print(ConsoleReport.PRComments.get_creation_success(comment_dict))
            return comment_dict

        except Exception as e:
            print(ConsoleReport.PRComments.get_creation_error(e))

    def _delete_previous_pr_comment(self, comment_id, content_provider):
        """Delete the previous temcheck comment of the PR.

        Useful if the comments stack up and create clutter, in which case
        only the last comment will be kept.

        :param int comment_id: the ID of the comment to leave intact
        :param BaseContentProvider content_provider: the object that has
            the ability to delete PR comments
        :return: True if the previous comment was deleted, False otherwise
        :rtype: bool
        """
        try:
            print()
            print(ConsoleReport.PRComments.get_deletion_pre_run())
            success = content_provider.delete_previous_pr_comment(comment_id)
            if success:
                print(ConsoleReport.PRComments.get_deletion_success())
            else:
                print(ConsoleReport.PRComments.get_deletion_failure())

            return success

        except Exception as e:
            print(ConsoleReport.PRComments.get_deletion_error(e))
