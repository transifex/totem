from typing import Type, Union

from totem.checks.config import CheckConfig
from totem.checks.results import STATUS_ERROR, STATUS_FAIL, STATUS_PASS, CheckResult


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

    def __init__(self, config: CheckConfig):
        """Constructor.

        :param CheckConfig config: the configuration to use when performing the check
            in case specific things need to be taken into account
        """
        self._config = config

    def run(self, content: dict) -> CheckResult:
        """Execute the check for the current parameters and return the result.

        :param dict content: contains parameters with the actual content to check,
            e.g. the commit message string for a checker that deals with commit messages
        :return: the result of performing the check
        :rtype: CheckResult
        """
        raise NotImplementedError()

    @property
    def check_type(self) -> str:
        return self._config.check_type

    def _from_config(self, name: str, default=None):
        """Return a parameter from the configuration options dictionary.

        If the options dictionary does not contain an entry with this name,
        it returns the `default` value provided in the call,
        otherwise the return value of _default_config().
        If no value is provider there either, it returns `None`.
        """
        default = default if default is not None else self._default_config(name)
        return self._config.options.get(name, default)

    def _default_config(self, name: str):
        """Return the default value that corresponds to the given option name.

        By default, this value is always `None`. Subclasses can override this
        functionality and provide custom values depending on the option name.
        """
        return None

    def _get_success(self, **details) -> CheckResult:
        """Return a successful result.

        This means that the check was executed and passed.
        """
        return CheckResult(self._config, STATUS_PASS, **details)

    def _get_failure(self, error_code: str, message: str, **details) -> CheckResult:
        """Return a failed result.

        This means that the check was executed and failed."""
        return CheckResult(
            self._config, STATUS_FAIL, error_code=error_code, message=message, **details
        )

    def _get_error(self, error_code: str, message: str, **details) -> CheckResult:
        """Return an erroneous result.

        This means that the check could not execute due to an error.
        """
        return CheckResult(
            self._config,
            STATUS_ERROR,
            error_code=error_code,
            message=message,
            **details,
        )


class CheckFactory:
    """Responsible for creating Check subclasses.

    Allows clients to add custom functionality, by providing a custom
    Check subclass, tied to a custom configuration type.
    """

    def __init__(self):
        self._checks = {}

    def register(self, config_type: str, check_class: type):
        """Register the given check class for the given configuration type.

        Allows clients to add custom functionality, by providing a custom
        Check subclass, tied to a custom configuration type.

        :param str config_type: an identifier that will be associated with
            the given check
        :param type check_class: the class that will be used to create
            an instance from; needs to be a Check subclass
        """
        self._checks[config_type] = check_class

    def create(self, config: CheckConfig) -> Union[Check, None]:
        """Create the proper Check subclass based on the given configuration.

        :param CheckConfig config: the configuration object to use
        :return: returns a check object
        :rtype: Check
        """
        config_type = config.check_type

        cls: Type[Check] = self._checks.get(config_type, None)
        if cls is None:
            return None

        return cls(config)
