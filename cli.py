import click
import json
import sys

from temcheck.checks.suite import CheckSuite
from temcheck.github.content import ContentProviderFactory
from temcheck.github.utils import parse_pr_url


def print_result(result):
    """Pretty-print the given result.

    :param CheckResult result:
    """
    if result.success:
        print('[{}] ... {}'.format(
            result.config.check_type,
            result.status.upper()
        ))
    else:
        print('[{}] ... {}'.format(result.config.check_type, result.status.upper()))
        print('Error code: {}'.format(result.error_code))
        print('Details:')
        print(json.dumps(result.details, sort_keys=True, indent=4))
        print()


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

    print('Will run {} checks'.format(len(config.keys())))
    suite = CheckSuite(config, factory)
    suite.run()

    errors = suite.results.errors
    print('\nErrors: {}\n-----------------'.format(len(errors)))
    for result in errors:
        print_result(result)

    warnings = suite.results.warnings
    print('\nWarnings: {}\n-----------------'.format(len(warnings)))
    for result in warnings:
        print_result(result)

    successful = suite.results.successful
    print('\nSuccessful checks: {}\n-----------------'.format(len(successful)))
    for result in successful:
        print_result(result)

    print('\n')

    if errors:
        sys.exit(1)
