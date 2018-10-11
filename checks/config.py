

class CheckConfig:
    """Represents the configuration of a single check.

    A single check can be something like the commit message.
    """

    def __init__(self, id, group=None, **options):
        """
        Constructor.

        `options` must be a dictionary with all necessary parameters for each check.
        Each check can have different parameters.

        :param str id: a unique ID that identifies this check
        :param str group: the name of the group this check belongs to
            e.g. 'pr' or 'commit'
        :param dict options: a dictionary with all configuration options
        """
        self.id = id
        self.group = group
        self.options = options
