"""Contains functionality related to retrieving the content to check against
certain rules.

This module includes content providers, which are classes that know how to
look for information from Github, that is necessary for performing checks.

Ideally this should be abstracted so that it does not depend on Github,
but rather any Git service. For now this is tightly coupled with
the Github functionality.
"""

from functools import lru_cache
from typing import Type, Union

from github.PullRequest import PullRequest
from totem.checks.checks import (
    TYPE_BRANCH_NAME,
    TYPE_COMMIT_MESSAGE,
    TYPE_PR_BODY_CHECKLIST,
    TYPE_PR_BODY_EXCLUDES,
    TYPE_PR_BODY_INCLUDES,
    TYPE_PR_TITLE,
)
from totem.checks.content import (
    BaseContentProvider,
    BaseGitServiceContentProviderFactory,
)
from totem.checks.core import Check
from totem.github import github_service
from totem.reporting.pr import PRCommentReport


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
    def get_pr(self) -> PullRequest:
        """Return the pull request object.

        :rtype: github.PullRequest.PullRequest
        """
        return github_service().get_pr(self.repo_name, self.pr_number)


class GithubPRContentProvider(GithubContentProvider):
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
    def get_content(self) -> dict:
        """Return a dictionary that contains various information about the PR."""
        pr = self.get_pr()
        return {'branch': pr.head.ref, 'title': pr.title, 'body': pr.body}

    def create_pr_comment(self, body: str) -> dict:
        """Create a comment on a pull request.

        :param str body: the body of the comment
        :return: a dictionary with information about the created comment
        :rtype: dict
        """
        if self.repo_name is None:
            return {}
        if self.pr_number is None:
            return {}
        return github_service().create_pr_comment(self.repo_name, self.pr_number, body)

    def delete_previous_pr_comment(self, latest_comment_id: int) -> bool:
        """Delete the previous totem comment on the PR.

        Only deletes 1 comment. `latest_comment_id` is given
        for ensuring that the newest comment will not be deleted.

        :param int latest_comment_id: the ID of the comment to leave intact
        :return: True if the previous comment was deleted, False otherwise
        :rtype: bool
        """
        if self.repo_name is None:
            return False
        if self.pr_number is None:
            return False

        comments = github_service().get_pr_comments(self.repo_name, self.pr_number)
        comments = [
            x
            for x in comments
            if x['body'].startswith(PRCommentReport.TITLE)
            and x['id'] != latest_comment_id
        ]
        comments = sorted(comments, key=lambda c: c['updated_at'])

        if not len(comments):
            return False

        comment = comments[-1]
        return github_service().delete_pr_comment(
            self.repo_name, self.pr_number, comment['id']
        )


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
    def get_content(self) -> dict:
        """Return a dictionary that contains various information about the commits."""
        commits = self.get_pr().get_commits()

        return {
            'commits': [
                {
                    'message': commit.commit.message,
                    'sha': commit.sha,
                    'url': commit.html_url,
                    'stats': {
                        'additions': commit.stats.additions,
                        'deletions': commit.stats.deletions,
                        'total': commit.stats.total,
                    },
                }
                for commit in commits
            ]
        }


class GithubContentProviderFactory(BaseGitServiceContentProviderFactory):
    """Responsible for creating the proper content provider for every type of check,
    specifically for the Github service.

    It's part of a mechanism for lazy retrieval of content from Github.
    The factory (instantly) creates provider objects that know how to get
    that content, but they don't start fetching it immediately. Anyone
    that gets hold of a provider object can command it to retrieve the content,
    which is an operation that might take time, since it often requires HTTP requests
    to the remote service.

    Allows clients to add custom functionality by registering new providers,
    associated with certain configuration types.
    """

    def create(self, check: Check) -> Union[BaseContentProvider, None]:
        """Return a content provider that can later provide all required content
        for a certain check to execute its actions.

        :param Check check: the check object to create a content provider for
        :return: a content provider
        :rtype: BaseContentProvider
        """
        params = {'repo_name': self.repo_name, 'pr_num': self.pr_num}

        cls: Type[BaseContentProvider] = self._providers.get(check.check_type, None)
        if cls is None:
            return None

        return cls(**params)

    def _get_defaults(self) -> dict:
        return {
            TYPE_BRANCH_NAME: GithubPRContentProvider,
            TYPE_PR_BODY_CHECKLIST: GithubPRContentProvider,
            TYPE_PR_TITLE: GithubPRContentProvider,
            TYPE_PR_BODY_EXCLUDES: GithubPRContentProvider,
            TYPE_PR_BODY_INCLUDES: GithubPRContentProvider,
            TYPE_COMMIT_MESSAGE: PRCommitsContentProvider,
        }
