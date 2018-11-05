"""Command Line Interface functionality. """

import sys

import click
import yaml
from temcheck.main import TemCheck


@click.command()
@click.option('-p', '--pr-url', required=True, type=str)
@click.option('-c', '--config-file', required=False, type=str)
@click.option('--details-url', required=False, type=str)
def main(pr_url, config_file=None, details_url=None):
    """Run all checks described in `config_file` for the PR on the given URL.

    :param str pr_url: the URL of the pull request as retrieved from the CI
    :param str config_file: the path of the configuration file,
        formatted in YAML, as found in contrib/config/sample.yml
    :param str details_url: the URL to visit for more details about the results
    """
    if not config_file:
        config_file = './contrib/config/default.yml'
    try:
        with open(config_file, 'r') as f:
            try:
                config = yaml.load(f)
            except Exception as e:
                print(
                    'Error parsing config file "{}" as a YAML document: {}'.format(
                        config_file, e
                    )
                )
                sys.exit(1)
    except Exception as e:
        print('Error opening config file: {}'.format(e))
        sys.exit(1)

    check = TemCheck(config_dict=config, pr_url=pr_url, details_url=details_url)
    results = check.run()
    if results.errors:
        sys.exit(1)
