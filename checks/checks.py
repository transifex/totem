from checks.config import CheckConfig
from checks.results import CheckResult, STATUS_PASS, STATUS_ERROR, STATUS_FAIL


ERROR_INVALID_CONTENT = 'invalid_content'
ERROR_INVALID_CONFIG = 'invalid_config'
ERROR_INVALID_BRANCH_NAME = 'invalid_branch_name'


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

    def __init__(self, config, content):
        """Constructor.

        :param CheckConfig config: the configuration to use when performing the check
            in case specific things need to be taken into account
        :param dict content: contains parameters with the actual content to check,
            e.g. the commit message string for a checker that deals with commit messages
        """
        self._config = config
        self._content = content

    def run(self):
        """Execute the check for the current parameters and return the result.

        :return: the result of performing the check
        :rtype: CheckResult
        """
        raise NotImplemented()

    def _from_config(self, name, default=None):
        """Return a parameter from the configuration options dictionary."""
        return self._config.options.get(name, default)

    def _from_content(self, name, default=None):
        """Return a parameter from the content dictionary."""
        return self._content.get(name, default)

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

    def run(self):
        """Check if a branch name has a certain prefix.

        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        prefix = self._from_config('prefix')
        branch_name = self._from_content('branch')

        if not branch_name:
            return self._get_error(
                ERROR_INVALID_CONTENT,
                message='Branch name not defined or empty',
            )

        if not prefix:
            return self._get_error(
                ERROR_INVALID_CONFIG,
                message='Branch name prefix not defined or empty',
            )

        success = branch_name.startswith(prefix)
        if not success:
            return self._get_failure(
                ERROR_INVALID_BRANCH_NAME,
                message='Branch name does not begin with "{}" prefix'.format(prefix)
            )

        return self._get_success()
