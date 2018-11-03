from functools import lru_cache


class BaseContentProvider:
    """The base class for all classes that want to provide content
    to be checked against some rules.

    Subclasses are meant to retrieve the content from whatever source
    is necessary, so that the Check object that will be performing the
    checks will have all necessary information.

    For each Check subclass there should be a corresponding ContentProvider
    subclass. e.g. for BranchNameCheck there should be a BranchNameContentProvider.
    """

    def __init__(self, **params):
        """Constructor.

        The caller can specify any number of custom parameters that are necessary
        for retrieving the proper content.
        """
        self.params = params

    @lru_cache(maxsize=None)
    def get_content(self):
        """Return a dictionary with all required content for the given check
        to perform its actions.

        The response is cached, so that this method can be called at
        any point of the process. Subclasses need to include the @lru_cache
        decorator.

        :return: a dictionary with all retrieved content
        :rtype: dict
        """
        raise NotImplemented()

    def create_pr_comment(self, body):
        """Create a comment on a pull request.

        :param str body: the body of the comment
        """
        raise NotImplemented()

    @property
    def repo_name(self):
        return self.params['repo_name']

    @property
    def pr_number(self):
        return self.params['pr_num']


class BaseContentProviderFactory:
    """A base class for classes that want to create content providers.

    Provides very simple functionality, i.e. storing necessary information
    in the constructor, to be later used to retrieve data from the
    corresponding Git service.
    """

    def __init__(self, repo_name, pr_num):
        """Constructor.

        :param str repo_name: the full name of the repository (<account>/<repo>)
        :param int pr_num: the identifier of the pull request
        """
        self.repo_name = repo_name
        self.pr_num = pr_num

    def create(self, check):
        """Return a content provider that can later provide all required content
        for a certain check to execute its actions.

        The return type depends on the Git service this factory supports.
        For example, for Github it should be content providers that use
        Github in order to retrieve all required information.

        :param Check check: the check object to create a content provider for
        :return: a content provider
        """
        raise NotImplemented()
