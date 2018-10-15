"""This is meant to be the main point of entry.

This is where the check suite is initialized. In order for everything to work,
we have to retrieve various information from the CI as well as from the environment
and feed them to a CheckSuite instance.
"""

from temcheck.checks.suite import CheckSuite
from temcheck.github.content import ContentProviderFactory
from temcheck.github.utils import parse_pr_url


def run_suite(config, pr_url):
    """Run all registered checks of the suite.

    :param dict config: the full configuration of the suite, as retrieved from the CI,
        formatted as described in CheckSuite
    :param str pr_url: the URL of the pull request as retrieved from the CI
    :return:
    """

    full_repo_name, pr_number = parse_pr_url(pr_url)
    factory = ContentProviderFactory(full_repo_name, pr_number)

    suite = CheckSuite(config, factory)
    suite.run()

    for result in suite.results.results.items():
        print(result)

    # TODO: do something with the results (e.g. block merging)
