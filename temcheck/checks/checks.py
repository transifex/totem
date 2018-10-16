import re

from temcheck.checks.results import (
    CheckResult, STATUS_PASS, STATUS_ERROR, STATUS_FAIL,
    ERROR_INVALID_CONFIG, ERROR_INVALID_CONTENT, ERROR_INVALID_BRANCH_NAME,
    ERROR_INVALID_PR_TITLE, ERROR_UNFINISHED_CHECKLIST, ERROR_FORBIDDEN_PR_BODY_TEXT,
    ERROR_MISSING_PR_BODY_TEXT,
)


TYPE_BRANCH_NAME = 'branch_name'
TYPE_PR_TITLE = 'pr_title'
TYPE_PR_BODY_CHECKLIST = 'pr_body_checklist'
TYPE_PR_BODY_INCLUDES = 'pr_body_includes'
TYPE_PR_BODY_EXCLUDES = 'pr_body_excludes'


class Check:
    """A base class for all classes that want to perform checks.

    Subclasses could be named like CommitMessageCheck, PRDescriptionCheck, etc.
    Each subclass should override the `run()` method.

    Subclasses can perform a very small, isolated check or perform multiple checks
    that are somehow "connected" together. For example, a subclass could only
    check if a branch name starts with a certain prefix, whereas another subclass could
    test 4-5 different things about a PR description that make sense to be grouped
    together.
    """

    def __init__(self, config):
        """Constructor.

        :param CheckConfig config: the configuration to use when performing the check
            in case specific things need to be taken into account
        """
        self._config = config

    def run(self, content):
        """Execute the check for the current parameters and return the result.

        :param dict content: contains parameters with the actual content to check,
            e.g. the commit message string for a checker that deals with commit messages
        :return: the result of performing the check
        :rtype: CheckResult
        """
        raise NotImplemented()

    @property
    def check_type(self):
        return self._config.check_type

    def _from_config(self, name, default=None):
        """Return a parameter from the configuration options dictionary."""
        return self._config.options.get(name, default)

    def _get_success(self, **details):
        """Return a successful result."""
        return CheckResult(
            self._config,
            STATUS_PASS,
            **details,
        )

    def _get_failure(self, error_code, message, **details):
        """Return a failed result."""
        return CheckResult(
            self._config,
            STATUS_FAIL,
            error_code=error_code,
            message=message,
            **details,
        )

    def _get_error(self, error_code, message, **details):
        """Return an erroneous result."""
        return CheckResult(
            self._config,
            STATUS_ERROR,
            error_code=error_code,
            message=message,
            **details,
        )


class BranchNameCheck(Check):
    """Checks whether or not a branch name follows a certain format."""

    def run(self, content):
        """Check if a branch name follows a certain format.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        pattern = self._from_config('pattern')
        branch_name = content.get('branch')

        if not branch_name:
            return self._get_error(
                ERROR_INVALID_CONTENT,
                message='Branch name not defined or empty',
            )

        if not pattern:
            return self._get_error(
                ERROR_INVALID_CONFIG,
                message='Branch name regex pattern not defined or empty',
            )

        success = re.search(pattern, branch_name) is not None
        if not success:
            return self._get_failure(
                ERROR_INVALID_BRANCH_NAME,
                message='Branch name "{}" doesn\'t match pattern: "{}"'.format(
                    branch_name,
                    pattern,
                )
            )

        return self._get_success()


class PRTitleCheck(Check):
    """Checks whether or not the title of a PR follows a certain format."""

    def run(self, content):
        """Check if a PR title follows a certain format.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        pattern = self._from_config('pattern')
        title = content.get('title')

        if not title:
            return self._get_error(
                ERROR_INVALID_CONTENT,
                message='PR title not defined or empty',
            )

        if not pattern:
            return self._get_error(
                ERROR_INVALID_CONFIG,
                message='PR title regex pattern not defined or empty',
            )

        success = re.search(pattern, title) is not None
        if not success:
            return self._get_failure(
                ERROR_INVALID_PR_TITLE,
                message='PR title "{}" doesn\'t match pattern: "{}"'.format(
                    title,
                    pattern,
                )
            )

        return self._get_success()


class PRBodyChecklistCheck(Check):
    """Checks whether or not there are unchecked checklist items in the body
    of a pull request.

    Many TEM templates include a checklist that the reviewer has to complete
    before the PR can be merged. Also, some developers use checklists as a TODO
    before merging a PR.

    This check makes sure that no item in a checklist is left uncheck, because
    this would mean that something is not complete yet.
    """

    def run(self, content):
        """Check if the body of a PR contains unchecked items.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        body = content.get('body')

        matches = re.findall('- \[ \]', body)
        if matches:
            return self._get_failure(
                ERROR_UNFINISHED_CHECKLIST,
                message='Found {} unfinished checklist items'.format(len(matches))
            )

        return self._get_success()


class PRBodyIncludesCheck(Check):
    """Makes sure that the PR body includes certain required strings.

    This is useful in cases there are "forbidden" things, that shouldn't
    be present inside a pull request body.

    This check tests again multiple regex patterns. It always checks them all
    and the result it returns includes all the ones that failed.
    """

    def run(self, content):
        """Check if the body of a PR contains specific text.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed, successful if
            all of the strings are included, failed otherwise
        :rtype: CheckResult
        """
        body = content.get('body')

        patterns = self._from_config('patterns', [])
        failed_items = []
        for pattern in patterns:
            success = re.search(pattern, body, re.MULTILINE) is not None
            if not success:
                failed_items.append(pattern)

        if failed_items:
            return self._get_failure(
                ERROR_MISSING_PR_BODY_TEXT,
                message='Required strings in PR body are missing: {}'.format(
                    ', '.join(['"{}"'.format(x) for x in failed_items])
                ),
            )

        return self._get_success()


class PRBodyExcludesCheck(Check):
    """Makes sure that the PR body does not include certain strings.

    This is useful in cases there are "forbidden" things, that shouldn't
    be present inside a pull request body.

    This check tests again multiple regex patterns. It always checks them all
    and the result it returns includes all the ones that failed.
    """

    def run(self, content):
        """Check if the body of a PR contains specific text.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed, successful if
            none of the strings are included, failed otherwise
        :rtype: CheckResult
        """
        body = content.get('body')

        patterns = self._from_config('patterns', [])
        failed_items = []
        for pattern in patterns:
            success = re.search(pattern, body, re.MULTILINE) is None
            if not success:
                failed_items.append(pattern)

        if failed_items:
            return self._get_failure(
                ERROR_FORBIDDEN_PR_BODY_TEXT,
                message='Forbidden strings found in PR body: {}'.format(
                    ', '.join(['"{}"'.format(x) for x in failed_items])
                ),
            )

        return self._get_success()


class CheckFactory:
    """Responsible for creating Check subclasses."""

    @staticmethod
    def create(config):
        """Create the proper Check subclass based on the given configuration.

        :param CheckConfig config: the configuration object to use
        :return: returns a check object
        :rtype: Check
        """
        config_type = config.check_type

        if config_type == TYPE_BRANCH_NAME:
            return BranchNameCheck(config)

        if config_type == TYPE_PR_TITLE:
            return PRTitleCheck(config)

        if config_type == TYPE_PR_BODY_CHECKLIST:
            return PRBodyChecklistCheck(config)

        if config_type == TYPE_PR_BODY_INCLUDES:
            return PRBodyIncludesCheck(config)

        if config_type == TYPE_PR_BODY_EXCLUDES:
            return PRBodyExcludesCheck(config)
