"""
Contains some wrappers with convenient API for performing
various actions on Github. Under the hood it uses the PyGithub
library (which in turn makes calls to the Github web API).
"""
from functools import lru_cache

from github.MainClass import Github


class GithubService:
    """Contains convenience methods and properties for Github-related
    functionality.

    An adapter to the functionality of the PyGithub library.
    """

    def __init__(self, access_token):
        """Constructor.

        :param str access_token: the access token to use for connecting
        """
        self.client = Github(login_or_token=access_token)

    @lru_cache(maxsize=None)
    def get_repo(self, repo_name):
        """Return the repository object with the given name.

        :param str repo_name: the full name of the repository
        :return: the repository or None if not found
        :rtype: github.Repository.Repository
        """
        return self.client.get_repo(repo_name)

    @lru_cache(maxsize=None)
    def get_pr(self, repo_name, pr_num):
        """Return the pull request object with the given number.

        :param str repo_name: the name of the repository the PR is in
        :param int pr_num: the identifier of the pull request
        :return: the pull request object
        :rtype: github.PullRequest.PullRequest
        """
        repo = self.get_repo(repo_name)
        if repo:
            return repo.get_pull(pr_num)

    def create_pr_comment(self, repo_name, pr_num, body):
        """Create a comment on the pull request with the given info.

        :param str repo_name:
        :param int pr_num:
        :param str body: the body of the comment to add
        :return: a dictionary with information about the created comment
        :rtype: dict
        """
        pr = self.get_pr(repo_name, pr_num)
        issue = pr.as_issue()
        comment = issue.create_comment(body)
        return {'html_url': comment.html_url}
