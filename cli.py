"""Command Line Interface functionality. """

import os.path
import sys

import click
import yaml
from temcheck.main import LocalTemCheck, PRTemCheck
from temcheck.reporting.console import Color


def run_checks(pr_url, config_file=None, details_url=None):
    """Run all checks described in `config_file` for the PR on the given URL.

    :param str pr_url: the URL of the pull request as retrieved from the CI
    :param str config_file: the path of the configuration file,
        formatted in YAML, as found in contrib/config/sample.yml
    :param str details_url: the URL to visit for more details about the results
    """
    if not config_file:
        if os.path.isfile('.temcheck.yml'):
            config_file = '.temcheck.yml'
        else:
            config_file = './contrib/config/default.yml'
    try:
        with open(config_file, 'r') as f:
            try:
                config = yaml.load(f)
            except Exception as e:
                print(
                    Color.format(
                        '[error]Error parsing config file "{}" as a YAML document: '
                        '{}[end]'.format(config_file, e)
                    )
                )
                sys.exit(1)
    except Exception as e:
        print(Color.format('[error]Error opening config file: {}[end]'.format(e)))
        sys.exit(1)

    if pr_url:
        check = PRTemCheck(config_dict=config, pr_url=pr_url, details_url=details_url)
    else:
        check = LocalTemCheck(config_dict=config)

    results = check.run()
    if results.errors:
        sys.exit(1)


@click.command()
@click.option('-p', '--pr-url', required=False, type=str)
@click.option('-c', '--config-file', required=False, type=str)
@click.option('--details-url', required=False, type=str)
def main(pr_url, config_file=None, details_url=None):
    """Run all checks described in `config_file`.

    If a URL of a pull request is given, it performs all checks on it.
    If no such URL is given, the checks run locally.

    If no `config_file` is given, it attempts to use `.temcheck.yml`.
    If that is not found, it defaults to `contrib/config/default.yml`.

    A command line function.

    :param str pr_url: the URL of the pull request
    :param str config_file: the path of the configuration file,
        formatted in YAML, as found in contrib/config/sample.yml
    :param str details_url: the URL to visit for more details about the results
    """
    run_checks(pr_url=pr_url, config_file=config_file, details_url=details_url)