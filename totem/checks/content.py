from functools import lru_cache
from typing import Dict, Union

from totem.checks.checks import Check


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
        self.params: Dict[str, Union[str, int]] = params

    @lru_cache(maxsize=None)
    def get_content(self) -> dict:
        """Return a dictionary with all required content for the given check
        to perform its actions.

        The response is cached, so that this method can be called at
        any point of the process. Subclasses need to include the @lru_cache
        decorator.

        :return: a dictionary with all retrieved content
        :rtype: dict
        """
        raise NotImplementedError()

    def create_pr_comment(self, body: str) -> dict:
        """Create a comment on a pull request.

        :param str body: the body of the comment
        """
        raise NotImplementedError()

    @property
    def repo_name(self) -> Union[str, None]:
        name = self.params.get('repo_name', None)
        return str(name) if name else None

    @property
    def pr_number(self) -> Union[int, None]:
        num = self.params.get('pr_num', None)
        return int(num) if num is not None else None

    def delete_previous_pr_comment(self, latest_comment_id: int) -> bool:
        """Delete the previous totem comment on the PR.

        TODO: This was added here temporarily in order to silence type checking
        TODO: Create a more proper architecture for this

        :param int latest_comment_id: the ID of the comment to leave intact
        :return: True if the previous comment was deleted, False otherwise
        :rtype: bool
        """
        return False


class BaseGitContentProviderFactory:
    """A base class for classes that want to create content providers.

    A content provider is responsible for providing content
    retrieved from Git, either from a local Git repository
    or a Git service.
    """

    def __init__(self):
        self._providers = {}
        self._register_defaults()

    def register(self, check_type: str, provider_class: type):
        """Register the given provider class for the given id.

        Allows clients to add custom functionality, by providing a custom
        GithubContentProvider subclass, tied to a custom string id.

        :param str check_type: the type of the check to associate this
            provider class with
        :param type provider_class: the class that will be used to create
            an instance from; needs to be a GithubContentProvider subclass
        """
        self._providers[check_type] = provider_class

    def create(self, check: Check) -> Union[BaseContentProvider, None]:
        """Return a content provider that can later provide all required content
        for a certain check to execute its actions.

        :param Check check: the check object to create a content provider for
        :return: a content provider
        :rtype: BaseContentProvider
        """
        raise NotImplementedError()

    def _register_defaults(self):
        """Register all default checks."""
        for provider_id, provider_class in self._get_defaults().items():
            self.register(provider_id, provider_class)

    def _get_defaults(self) -> dict:
        """Return a dictionary of default checks.

        Subclasses can provide the actual checks.

        :rtype: dict
        """
        return {}


class BaseGitServiceContentProviderFactory(BaseGitContentProviderFactory):
    """A base class for classes that want to create content providers
    that use a Git service (e.g. Github).

    Provides very simple functionality, i.e. storing necessary information
    in the constructor, to be later used to retrieve data from the
    corresponding Git service.
    """

    def __init__(self, repo_name: str, pr_num: int):
        """Constructor.

        :param str repo_name: the full name of the repository (<account>/<repo>)
        :param int pr_num: the identifier of the pull request
        """
        super().__init__()
        self.repo_name = repo_name
        self.pr_num = pr_num

    def create(self, check: Check) -> Union[BaseContentProvider, None]:
        """Return a content provider that can later provide all required content
        for a certain check to execute its actions.

        The return type depends on the Git service this factory supports.
        For example, for Github it should be content providers that use
        Github in order to retrieve all required information.

        :param Check check: the check object to create a content provider for
        :return: a content provider
        :rtype: BaseContentProvider
        """
        raise NotImplementedError()
