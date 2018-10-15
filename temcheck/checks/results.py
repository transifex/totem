STATUS_PASS = 'pass'  # The check passed with success
STATUS_FAIL = 'fail'  # The check was executed properly but failed
STATUS_ERROR = 'error'  # The check could not be executed because of an error


class CheckResult:
    """Contains the results of a single Check that was performed."""

    def __init__(self, config, status, error_code=None, **details):
        """Constructor.

        :param CheckConfig config: the related configuration with which the check was run
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

    def __str__(self):
        return 'CheckResult type={}, status={}, error_code={}, details={}'.format(
            self.config.check_type,
            self.status,
            self.error_code,
            self.details,
        )

    def __repr__(self):
        return self.__str__()


class CheckSuiteResults:
    """Contains the results of all the checks of a check suite that were executed."""

    def __init__(self):
        self.results = {}

    def add(self, result):
        """Store the given result.

        :param CheckResult result: the result to store
        """
        self.results[result.config.check_type] = result
