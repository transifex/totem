import os

from git import Repo
from temcheck.checks.checks import TYPE_BRANCH_NAME, TYPE_COMMIT_MESSAGE
from temcheck.checks.content import BaseContentProvider, BaseGitContentProviderFactory


class BranchContentProvider(BaseContentProvider):
    def get_content(self):
        """Return a dictionary that contains the current branch name."""
        repo = Repo(os.getcwd())
        branch_name = repo.head.ref.name
        return {'branch': branch_name}


class CommitsContentProvider(BaseContentProvider):
    def get_content(self):
        """Return a dictionary that contains information about all commits
        of the current branch (max 50)."""
        repo = Repo(os.getcwd())
        branch_name = repo.head.ref.name
        last_commit = repo.commit(branch_name)
        parent_ref = last_commit.parents[0]

        # We only want the commits of the current branch, from the parent
        # to the tip of the branch, e.g. master...my-feature-branch
        rev = '{}...{}'.format(parent_ref, branch_name)
        commits = list(repo.iter_commits(rev, max_count=50))

        return {
            'commits': [
                {
                    'message': commit.message,
                    'sha': commit.hexsha,
                    'url': '',
                    'stats': {
                        'additions': commit.stats.total['insertions'],
                        'deletions': commit.stats.total['deletions'],
                        'total': commit.stats.total['lines'],
                    },
                }
                for commit in commits
            ]
        }


class GitContentProviderFactory(BaseGitContentProviderFactory):
    """Responsible for creating the proper content provider for every type of check,
    specifically for local Git repositories.

    This is part of a mechanism for lazy retrieval of content from services
    like Github. The factory (instantly) creates provider objects that know how to get
    that content, but they don't start fetching it immediately. Anyone
    that gets hold of a provider object can command it to retrieve the content,
    which is an operation that might take time, since it often requires HTTP requests
    to the remote service.

    Allows clients to add custom functionality by registering new providers,
    associated with certain configuration types.
    """

    def create(self, check):
        """Return a content provider that can later provide all required content
        for a certain check to execute its actions.

        :param Check check: the check object to create a content provider for
        :return: a content provider
        :rtype: BaseContentProvider
        """
        cls = self._providers.get(check.check_type, None)
        if cls is None:
            return None

        return cls()

    def _get_defaults(self):
        return {
            TYPE_BRANCH_NAME: BranchContentProvider,
            TYPE_COMMIT_MESSAGE: CommitsContentProvider,
        }
