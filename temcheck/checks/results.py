from temcheck.checks.config import FAILURE_LEVEL_ERROR, FAILURE_LEVEL_WARNING

STATUS_PASS = 'pass'  # The check passed with success
STATUS_FAIL = 'fail'  # The check was executed properly but failed
STATUS_ERROR = 'error'  # The check could not be executed because of an error

ERROR_INVALID_CONTENT = 'invalid_content'
ERROR_INVALID_CONFIG = 'invalid_config'
ERROR_GENERIC = 'generic_error'

ERROR_INVALID_BRANCH_NAME = 'invalid_branch_name'
ERROR_INVALID_PR_TITLE = 'invalid_pr_title'
ERROR_UNFINISHED_CHECKLIST = 'unfinished_checklist'
ERROR_FORBIDDEN_PR_BODY_TEXT = 'forbidden_pr_body_text'
ERROR_MISSING_PR_BODY_TEXT = 'missing_pr_body_text'
ERROR_INVALID_COMMIT_MESSAGE_FORMAT = 'invalid_commit_message_format'


class CheckResult:
    """Contains the results of a single Check that was performed."""

    def __init__(self, config, status, error_code=None, **details):
        """Constructor.

        :param CheckConfig config: the related configuration with which the
            check was run
        :param str status: the status that shows how the check went,
            one of STATUS_PASS, STATUS_FAIL, STATUS_ERROR
        :param str error_code: a string that
        """
        self.config = config
        self.status = status
        self.error_code = error_code
        self.details = details

    @property
    def success(self):
        """True if the check succeeded, False if it failed or didn't finish because
        of an error."""
        return self.status == STATUS_PASS

    @property
    def failure_level(self):
        """Defines how to handle a failed (or erroneous) result.

        For example, if it should block merging or just show a warning message.
        """
        return self.config.failure_level

    def __str__(self):
        return 'CheckResult type={}, status={}, error_code={}, details={}'.format(
            self.config.check_type, self.status, self.error_code, self.details
        )

    def __repr__(self):
        return self.__str__()


class CheckSuiteResults:
    """Contains the results of all the checks of a check suite that were executed."""

    def __init__(self):
        self._failed = []
        self._successful = []

    def add(self, result):
        """Store the given result.

        :param CheckResult result: the result to store
        """
        if result.success:
            self._successful.append(result)
        else:
            self._failed.append(result)

    @property
    def successful(self):
        """A list of all CheckResult objects that passed the check."""
        return self._successful

    @property
    def failed(self):
        """A list of all CheckResult objects that failed the check."""
        return self._failed

    @property
    def warnings(self):
        """A list of all CheckResult objects that failed the check
        and are considered to be non-required (warning level)."""
        return [
            result
            for result in self._failed
            if result.failure_level == FAILURE_LEVEL_WARNING
        ]

    @property
    def errors(self):
        """A list of all CheckResult objects that failed the check
        and are considered to be required (error level)."""
        return [
            result
            for result in self._failed
            if result.failure_level == FAILURE_LEVEL_ERROR
        ]