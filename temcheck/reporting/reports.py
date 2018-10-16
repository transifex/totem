import json

from temcheck.checks.results import CheckSuiteResults
from temcheck.checks.suite import CheckSuite


def _print_result(result):
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


def print_pre_run(config):
    """Print a message before running the checks.

    :param dict config: the configuration that will be used
    """
    check_types = config.keys()
    print()
    print('About to check if the current PR follows the TEM (https://tem.transifex.com/)')
    print('\nWill run {} checks:'.format(len(check_types)))
    for check_type in check_types:
        print(' - {}'.format(check_type))

    print()


def print_detailed_results(results):
    """Print all results in detail.

    :param CheckSuiteResults results: the object that contains the results
    """
    errors = results.errors
    warnings = results.warnings
    successful = results.successful

    print('Results:')
    print(' - Errors: {}'.format(len(errors)))
    print(' - Warnings: {}'.format(len(warnings)))
    print(' - Successful: {}'.format(len(successful)))
    print()

    print('\nErrors: {}\n-----------------'.format(len(errors)))
    for result in errors:
        _print_result(result)

    warnings = results.warnings
    print('\nWarnings: {}\n-----------------'.format(len(warnings)))
    for result in warnings:
        _print_result(result)

    successful = results.successful
    print('\nSuccessful checks: {}\n-----------------'.format(len(successful)))
    for result in successful:
        _print_result(result)

    print('\n')

