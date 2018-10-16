import click
import json
import sys

from temcheck.checks.suite import CheckSuite
from temcheck.github.content import ContentProviderFactory
from temcheck.github.utils import parse_pr_url
from temcheck.reporting.reports import print_detailed_results, print_pre_run


@click.command()
@click.option('-p', '--pr-url', required=True, type=str)
@click.option('-c', '--config-file', required=True, type=str)
def main(pr_url, config_file):
    """Run all checks described in `config_file` for the PR on the given URL.

    :param str pr_url: the URL of the pull request as retrieved from the CI
    :param str config_file: the path of the configuration file,
        formatted as as described in CheckSuite (in JSON format)
    """
    full_repo_name, pr_number = parse_pr_url(pr_url)
    factory = ContentProviderFactory(full_repo_name, pr_number)
    try:
        with open(config_file, 'r') as f:
            try:
                config = json.load(f)
            except Exception as e:
                print('Error parsing config file as a JSON document, "%s"' % e)
                sys.exit(1)
    except Exception as e:
        print('Error opening config file, "%s"' % e)
        sys.exit(1)

    print_pre_run(config)
    suite = CheckSuite(config, factory)
    suite.run()
    print_detailed_results(suite.results)

    if suite.results.errors:
        sys.exit(1)
