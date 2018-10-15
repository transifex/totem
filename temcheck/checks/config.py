
FAILURE_LEVEL_WARNING = 'warning'
FAILURE_LEVEL_ERROR = 'error'


class CheckConfig:
    """Represents the configuration of a single check.

    A single check can be something like the format of a branch name.

    The config class is agnostic to specific checks; it keeps the configuration
    in a generic dictionary. It is up to the consumer of this class to know
    what type of information to retrieve, based on the ID (key) of the config.

    For example, a class that wants to check if a branch name has a certain prefix
    should know the proper keys to look for in the config object (in this case
    the branch name and the expected prefix).
    """

    def __init__(self, check_type, failure_level, **options):
        """
        Constructor.

        `options` must be a dictionary with all necessary parameters for each check.
        Each check can have different parameters.

        :param str check_type: a unique string that shows what type of check
            this is
        :param str failure_level: defines how a failed check should be treated
            (an error would block merging, whereas a warning would not)
        :param dict options: a dictionary with all configuration options
        """
        self.check_type = check_type
        self.failure_level = failure_level
        self.options = options
