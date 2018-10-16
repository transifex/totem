"""Contains functionality related to retrieving the content to check against
certain rules.

This module includes content providers, which are classes that know how to
look for information from Github, that is necessary for performing checks.

Ideally this should be abstracted so that it does not depend on Github,
but rather any Git service. For now this is tightly coupled with
the Github functionality.
"""

from functools import lru_cache

from temcheck.checks.checks import (
    Check, TYPE_BRANCH_NAME, TYPE_PR_BODY_CHECKLIST, TYPE_PR_TITLE,
    TYPE_PR_BODY_EXCLUDES, TYPE_PR_BODY_INCLUDES, TYPE_COMMIT_MESSAGE,
)
from temcheck.checks.content import BaseContentProviderFactory, BaseContentProvider
from temcheck.github import github_service


class GithubContentProvider(BaseContentProvider):
    """A base class for all content providers that use Github.

    Provides some convenience functionality.
    """

    def __init__(self, **params):
        """Constructor.

        The caller can specify any number of custom parameters that are necessary
        for retrieving the proper content.
        """
        super().__init__(**params)

    @lru_cache(maxsize=None)
    def get_pr(self):
        """Return the pull request object.

        :rtype: github.PullRequest.PullRequest
        """
        return github_service().get_pr(self.repo_name, self.pr_number)


class PRContentProvider(GithubContentProvider):
    """Retrieves information of a pull request from Github.

    Contains all information that is necessary to perform related checks.
    Makes only one request to the Github API.

    If a check object needs more information that is available without doing
    any extra request, the information should be added here in new keys
    in the returned dictionary. If extra requests are necessary, a new content
    provider subclass must be created, to avoid making redundant requests
    for all PR-based content providers.
    """

    @lru_cache(maxsize=None)
    def get_content(self):
        """Return a dictionary that contains various information about the PR."""
        pr = self.get_pr()
        return {
            'branch': pr.head.ref,
            'title': pr.title,
            'body': pr.body,
        }


class PRCommitsContentProvider(GithubContentProvider):
    """Retrieves information of all commits of a pull request from Github.

    Contains all information that is necessary to perform related on commit
    checks. Makes one request to the Github API for retrieving the PR info
    (if not already cached) and another request for retrieving the commit info.

    If a check object needs more information that is available without doing
    any extra request, the information should be added here in new keys
    in the returned dictionary. If extra requests are necessary, a new content
    provider subclass must be created, to avoid making redundant requests
    for all PR-based content providers.
    """

    @lru_cache(maxsize=None)
    def get_content(self):
        """Return a dictionary that contains various information about the commits."""
        commits = self.get_pr().get_commits()

        return {
            'commits': [
                {
                    'message': commit.commit.message,
                    'sha': commit.sha,
                    'url': commit.html_url
                }
                for commit in commits
            ],
        }


class ContentProviderFactory(BaseContentProviderFactory):
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
        :rtype: BaseContentProvider
        """
        params = {
            'repo_name': self.repo_name,
            'pr_num': self.pr_num,
        }

        pr_types = (
            TYPE_BRANCH_NAME,
            TYPE_PR_BODY_CHECKLIST,
            TYPE_PR_TITLE,
            TYPE_PR_BODY_EXCLUDES,
            TYPE_PR_BODY_INCLUDES,
        )
        if check.check_type in pr_types:
            return PRContentProvider(**params)

        if check.check_type == TYPE_COMMIT_MESSAGE:
            return PRCommitsContentProvider(**params)
