"""
Contains some wrappers with convenient API for performing
various actions on Github. Under the hood it uses the PyGithub
library (which in turn makes calls to the Github web API).
"""
from functools import lru_cache
from typing import List

from github.MainClass import Github
from github.Repository import Repository


class GithubService:
    """Contains convenience methods and properties for Github-related
    functionality.

    An adapter to the functionality of the PyGithub library.
    """

    def __init__(self, access_token: str):
        """Constructor.

        :param str access_token: the access token to use for connecting
        """
        self.client = Github(login_or_token=access_token)

    @lru_cache(maxsize=None)
    def get_repo(self, repo_name: str) -> Repository:
        """Return the repository object with the given name.

        :param str repo_name: the full name of the repository
        :return: the repository or None if not found
        :rtype: github.Repository.Repository
        """
        return self.client.get_repo(repo_name)

    @lru_cache(maxsize=None)
    def get_pr(self, repo_name: str, pr_num: int):
        """Return the pull request object with the given number.

        :param str repo_name: the name of the repository the PR is in
        :param int pr_num: the identifier of the pull request
        :return: the pull request object
        :rtype: PullRequest
        """
        repo = self.get_repo(repo_name)
        if repo:
            return repo.get_pull(pr_num)

    def create_pr_comment(self, repo_name: str, pr_num: int, body: str) -> dict:
        """Create a comment on the pull request with the given info.

        :param str repo_name: the name of the repository the PR is in
        :param int pr_num: the identifier of the pull request
        :param str body: the body of the comment to add
        :return: a dictionary with information about the created comment
        :rtype: dict
        """
        pr = self.get_pr(repo_name, pr_num)
        issue = pr.as_issue()
        comment = issue.create_comment(body)
        return {'id': comment.id, 'html_url': comment.html_url}

    def get_pr_comments(self, repo_name: str, pr_num: int) -> List[dict]:
        """Return a list of comments on the PR with the given number.

        :param str repo_name: the name of the repository the PR is in
        :param int pr_num: the identifier of the pull request
        :return: a list of all comments, formatted as:
            [
              {'id': <comment_id>, 'body': <body>, 'updated_at': <updated_at>},
              ...
            ]
        :rtype: list
        """
        pr = self.get_pr(repo_name, pr_num)
        issue = pr.as_issue()
        comments = issue.get_comments()
        return [
            {'id': comment.id, 'body': comment.body, 'updated_at': comment.updated_at}
            for comment in comments
        ]

    def delete_pr_comment(self, repo_name: str, pr_num: int, comment_id: int) -> bool:
        """Delete the PR comment with the given id

        :param str repo_name: the name of the repository the PR is in
        :param int pr_num: the identifier of the pull request
        :param int comment_id: the ID of the comment to delete
        :return: True if found and deleted successfully, False otherwise
        :rtype: bool
        """
        pr = self.get_pr(repo_name, pr_num)
        issue = pr.as_issue()
        comment = issue.get_comment(comment_id)
        if comment is None:
            return False

        comment.delete()
        return True
