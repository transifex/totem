"""Contains functionality related to retrieving the content to check against
certain rules.

This module includes content providers, which are classes that know how to
look for information from Github, that is necessary for performing checks.

Ideally this should be abstracted so that it does not depend on Github,
but rather any Git service. For now this is tightly coupled with
the Github functionality.
"""

from functools import lru_cache

from checks.checks import Check, TYPE_BRANCH_NAME


class ContentProvider:
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


class BranchNameContentProvider(ContentProvider):
    """Retrieves the branch name of a pull request from Github."""

    @lru_cache(maxsize=None)
    def get_content(self):
        """Return a dictionary that contains the current branch name."""
        return {
            'branch_name': self._get_branch_name()
        }

    def _get_branch_name(self):
        return ''  # TODO


class ContentProviderFactory:
    """Responsible for creating the proper content provider for every type of check.

    This is part of a mechanism for lazy retrieval of content from services
    like Github. The factory (instantly) creates provider objects that know how to get
    that content, but they don't start fetching it immediately. Anyone
    that gets hold of a provider object can command it to retrieve the content,
    which is an operation that might take time, since it often requires HTTP requests
    to the remote service.
    """

    def create(self, check):
        """Return a content provider that can later provide all required content
        for a certain check to execute its actions.

        :param Check check: the check object to create a content provider for
        :return: a content provider
        :rtype: ContentProvider
        """
        if check.check_type == TYPE_BRANCH_NAME:
            return BranchNameContentProvider()

