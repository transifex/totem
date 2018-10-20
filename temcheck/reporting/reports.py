import pyaml

from temcheck.checks.results import CheckSuiteResults, STATUS_FAIL


class Color:
    HEADER = '\033[36m'
    CHECK_ITEM = '\033[1m'
    PASS = '\033[32m'
    FAIL = '\033[91m'
    ERROR = '\033[31m'
    WARNING = '\033[33m'
    END = '\033[0m'

    @staticmethod
    def print(string):
        """Print to the console with color support."""
        string = string.replace('[check]', Color.CHECK_ITEM)\
            .replace('[h]', Color.HEADER)\
            .replace('[end]', Color.END)\
            .replace('[pass]', Color.PASS)\
            .replace('[error]', Color.ERROR)\
            .replace('[fail]', Color.FAIL)\
            .replace('[warning]', Color.WARNING)
        print(string)


def _print_result(result):
    """Pretty-print the given result.

    :param CheckResult result:
    """
    if result.success:
        Color.print('[check][{}][end] ... [pass]{}[end]'.format(
            result.config.check_type,
            result.status.upper(),
        ))
    else:
        if result.status == STATUS_FAIL:
            Color.print('[check][{}][end] ... [fail]{}[end]'.format(
                result.config.check_type,
                result.status.upper()
            ))
        else:
            Color.print('[check][{}][end] ... [error]{}[end]'.format(
                result.config.check_type,
                result.status.upper()
            ))
        Color.print('[h]Error code[end]: {}'.format(result.error_code))
        Color.print('[h]Details[end]:')
        pyaml.p(result.details)
        print()


def print_pre_run(config):
    """Print a message before running the checks.

    :param dict config: the configuration that will be used
    """
    check_types = config.keys()
    print()
    print(
        'About to check if the current PR follows the TEM (https://tem.transifex.com/)'
    )
    print('\nWill run {} checks:'.format(len(check_types)))
    for check_type in check_types:
        Color.print(' - [check][{}][end]'.format(check_type))

    print()


def print_detailed_results(results):
    """Print all results in detail.

    :param CheckSuiteResults results: the object that contains the results
    """
    errors = results.errors

    Color.print('\n[error]Failures ({})[end]\n-----------------'.format(len(errors)))
    for result in errors:
        _print_result(result)

    warnings = results.warnings
    Color.print(
        '\n[warning]Warnings ({})[end]\n-----------------'.format(len(warnings))
    )
    for result in warnings:
        _print_result(result)

    successful = results.successful
    Color.print(
        '\n[pass]Successful checks ({})[end]\n-----------------'.format(len(successful))
    )
    for result in successful:
        _print_result(result)

    print('\n\n')
    print('SUMMARY')
    print('-------')
    Color.print('[fail]Failures ({})[end] - These need to be fixed'.format(len(errors)))
    for result in errors:
        Color.print('- [check][{}][end]'.format(result.config.check_type))
    print()

    Color.print(
        '[warning]Warnings({})[end] - '
        'Fixing these is optional and may not be applicable'.format(
            len(warnings)
        )
    )
    for result in warnings:
        Color.print('- [check][{}][end]'.format(result.config.check_type))
    print()

    Color.print('[pass]Successful ({})[end]'.format(len(successful)))
    for result in successful:
        Color.print('- [check][{}][end]'.format(result.config.check_type))
    print()

    print('\n')

