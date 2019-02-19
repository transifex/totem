import os
import re
from functools import lru_cache
from typing import Type, Union

from git import Repo
from totem.checks.checks import TYPE_BRANCH_NAME, TYPE_COMMIT_MESSAGE
from totem.checks.content import BaseContentProvider, BaseGitContentProviderFactory
from totem.checks.core import Check


class BranchContentProvider(BaseContentProvider):
    @lru_cache(maxsize=None)
    def get_content(self) -> dict:
        """Return a dictionary that contains the current branch name.

        :return: the current branch name, in a dictionary like:
            {'branch': <branch_name>}
        :rtype: dict
        """
        repo = Repo(os.getcwd())
        if repo.head.is_detached:
            branch_name = None
        else:
            branch_name = repo.head.ref.name
        
        return {'branch': branch_name}


class CommitsContentProvider(BaseContentProvider):
    @lru_cache(maxsize=None)
    def get_content(self) -> dict:
        """Return a dictionary that contains information about all commits
        of the current branch (max 50).

        :return: the information in a dictionary format as follows:
            {
              'commits': [
                {
                  'message': <message>,
                  'sha': <sha>,
                  'url': '',
                  'stats': {
                    'additions': <total_additions>,
                    'deletions': <total_deletions>,
                    'total': <total_lines>,
                  },
                },
                {
                  ...
                },
              ],
            }
        :rtype: dict
        """
        repo = Repo(os.getcwd())
        if repo.head.is_detached:
            branch_name = repo.head.commit.hexsha
        else:
            branch_name = repo.head.ref.name
        last_commit = repo.commit(branch_name)
        parent_ref = last_commit.parents[0]

        # We only want the commits of the current branch, from the parent
        # to the tip of the branch, e.g. master...my-feature-branch
        rev = '{}...{}'.format(parent_ref, branch_name)
        commits = list(repo.iter_commits(rev, max_count=50, no_merges=True))

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

    def create(self, check: Check) -> Union[BaseContentProvider, None]:
        """Return a content provider that can later provide all required content
        for a certain check to execute its actions.

        :param Check check: the check object to create a content provider for
        :return: a content provider
        :rtype: BaseContentProvider
        """
        cls: Type[BaseContentProvider] = self._providers.get(check.check_type, None)
        if cls is None:
            return None

        return cls()

    def _get_defaults(self) -> dict:
        return {
            TYPE_BRANCH_NAME: BranchContentProvider,
            TYPE_COMMIT_MESSAGE: CommitsContentProvider,
        }


class PreCommitBranchContentProvider(BaseContentProvider):
    @lru_cache(maxsize=None)
    def get_content(self) -> dict:
        """Return a dictionary that contains the current branch name.

        :return: the current branch name, in a dictionary like:
            {'branch': <branch_name>}
        :rtype: dict
        """
        repo = Repo(os.getcwd())
        branch_name = repo.head.ref.name
        return {'branch': branch_name}


class PreCommitCommitsContentProvider(BaseContentProvider):
    @lru_cache(maxsize=None)
    def get_content(self) -> dict:
        """Return a dictionary that contains information about
        the pending commit of the current branch.

        :return: the information in a dictionary format as follows:
            {
              'commits': [
                {
                  'message': <message>,
                  'sha': ',
                  'url': '',
                  'stats': {
                    'additions': <total_additions>,
                    'deletions': <total_deletions>,
                    'total': <total_lines>,
                  },
                },
              ],
            }
        :rtype: dict
        """
        repo = Repo(os.getcwd())
        git_dir = repo.git_dir

        # Find the pending commit message
        commit_msg_filepath = os.path.join(git_dir, 'COMMIT_EDITMSG')
        with open(commit_msg_filepath, 'r') as f:
            content = f.read()

        # Get the commit statistics
        diff = repo.git.diff('--cached', '--shortstat')
        regex = (
            '\s+(\d+) files? changed, '
            '(\d+) insertions?\(\+\), (\d+) deletions?\(\-\)'
        )
        result = re.match(regex, diff)
        if result:
            insertions = int(result.group(2))
            deletions = int(result.group(3))
        else:
            insertions, deletions = 0, 0

        return {
            'commits': [
                {
                    'message': content,
                    'sha': '',
                    'url': '',
                    'stats': {
                        'additions': insertions,
                        'deletions': deletions,
                        'total': insertions + deletions,
                    },
                }
            ]
        }


class PreCommitContentProviderFactory(BaseGitContentProviderFactory):
    """Responsible for creating the proper content provider for every type of check,
    specifically for local Git repositories amd a pre-commit setting.

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
        cls: Type[BaseContentProvider] = self._providers.get(check.check_type, None)
        if cls is None:
            return None

        return cls()

    def _get_defaults(self) -> dict:
        return {
            TYPE_BRANCH_NAME: PreCommitBranchContentProvider,
            TYPE_COMMIT_MESSAGE: PreCommitCommitsContentProvider,
        }
