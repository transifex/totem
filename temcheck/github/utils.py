from typing import Tuple


def parse_pr_url(url: str) -> Tuple[str, int]:
    """Parse the given pull request URL and return its information.

    :param str url: the PR URL from Github, formatted as:
        https://api.github.com/repos/<account>/<repo>/pulls/<pr_number>
    :return: the PR information as (full_repo_name, pr_number)
    :rtype: tuple
    """
    arr = url.split('/')
    full_repo_name = '{}/{}'.format(arr[-4], arr[-3])
    pr_num = int(arr[-1])

    return full_repo_name, pr_num
