"""Command Line Interface functionality. """

import os.path
import sys

import click
import yaml
from totem.main import LocalCheck, PRCheck, PreCommitLocalCheck
from totem.reporting.console import Color


def run_checks(
    pr_url: str,
    config_file: str = None,
    details_url: str = None,
    arguments: list = None,
):
    """Run all checks described in `config_file` for the PR on the given URL.

    :param str pr_url: the URL of the pull request as retrieved from the CI
    :param str config_file: the path of the configuration file,
        formatted in YAML, as found in contrib/config/sample.yml
    :param str details_url: the URL to visit for more details about the results
    :param list arguments: a list of optional arguments; if the list is empty,
        all commits of the current branch will be checked; otherwise,
        only the pending commit will be checked (as in a pre-commit fashion)
    """
    if not config_file:
        if os.path.isfile('.totem.yml'):
            config_file = '.totem.yml'
        else:
            package_root = os.path.split(__file__)[0]
            config_file = os.path.join(package_root, 'contrib/config/default.yml')
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

    print(
        'Running with arguments:\n'
        ' - PR URL: {pr_url}\n'
        ' - Config file path: {config_file}\n'
        ' - Details URL: {details_url}'.format(
            pr_url=pr_url if pr_url is None else '"{}"'.format(pr_url),
            config_file=(
                config_file if config_file is None else '"{}"'.format(config_file)
            ),
            details_url=(
                details_url if details_url is None else '"{}"'.format(details_url)
            ),
        )
    )
    if pr_url:
        print('Running in PRCheck mode')
        check = PRCheck(config_dict=config, pr_url=pr_url, details_url=details_url)
    else:
        if not arguments:
            print('Running in LocalCheck mode')
            check = LocalCheck(config_dict=config)
        else:
            print('Running in PreCommitLocalCheck mode')
            check = PreCommitLocalCheck(config_dict=config)

    results = check.run()
    if results.errors:
        sys.exit(1)


@click.command()
@click.option('-p', '--pr-url', required=False, type=str)
@click.option('-c', '--config-file', required=False, type=str)
@click.option('--details-url', required=False, type=str)
@click.argument('args', nargs=-1)
def main(
    pr_url: str, config_file: str = None, details_url: str = None, args: list = None
):
    """Run all checks described in `config_file`.

    If a URL of a pull request is given, it performs all checks on it.
    If no such URL is given, the checks run locally.

    If no `config_file` is given, it attempts to use `.totem.yml`.
    If that is not found, it defaults to `contrib/config/default.yml`.

    A command line function.

    :param str pr_url: the URL of the pull request
    :param str config_file: the path of the configuration file,
        formatted in YAML, as found in contrib/config/sample.yml
    :param str details_url: the URL to visit for more details about the results
    :param list args: necessary for pre-commit support
    """
    run_checks(
        pr_url=pr_url, config_file=config_file, details_url=details_url, arguments=args
    )
