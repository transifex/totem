"""Includes functionality for writing output on the console."""

import pyaml
from temcheck.checks.results import STATUS_FAIL
from temcheck.reporting import StringBuilder


class Color:
    """Convenience class for adding color to console output."""

    HEADER = '\033[36m'
    CHECK_ITEM = '\033[1m'
    PASS = '\033[32m'
    FAIL = '\033[91m'
    ERROR = '\033[31m'
    WARNING = '\033[33m'
    END = '\033[0m'

    @staticmethod
    def format(string):
        """Format the given string, adding color support."""
        return (
            string.replace('[check]', Color.CHECK_ITEM)
            .replace('[h]', Color.HEADER)
            .replace('[end]', Color.END)
            .replace('[pass]', Color.PASS)
            .replace('[success]', Color.PASS)
            .replace('[error]', Color.ERROR)
            .replace('[fail]', Color.FAIL)
            .replace('[warning]', Color.WARNING)
        )

    @staticmethod
    def print(string):
        """Print to the console with color support."""
        print(Color.format(string))


class ConsoleReport:
    """Creates reports to be used as console output when the checks run."""

    @staticmethod
    def get_pre_run_report(config, pr_url):
        """Print a message before running the checks.

        :param Config config: the configuration that will be used
        :param str pr_url: the URL of the pull request
        """
        check_types = config.check_configs.keys()
        builder = StringBuilder()
        builder.add()
        builder.add(
            'About to check if the following PR follows the TEM '
            '(https://tem.transifex.com/)'
        )
        builder.add('PR: {}'.format(pr_url))
        builder.add('\nWill run {} checks:'.format(len(check_types)))
        for check_type in check_types:
            builder.add(Color.format(' - [check][{}][end]'.format(check_type)))

        builder.add()
        return builder.render()

    @staticmethod
    def get_detailed_results(results):
        """Return a string with all results in detail.

        :param CheckSuiteResults results: the object that contains the results
        :return: the detailed string
        :rtype: str
        """
        errors = results.errors
        builder = StringBuilder()

        builder.add(
            Color.format(
                '\n[error]Failures ({})[end]\n-----------------'.format(len(errors))
            )
        )
        for result in errors:
            builder.add(ConsoleReport._format_result(result))

        warnings = results.warnings
        builder.add(
            Color.format(
                '\n[warning]Warnings ({})[end]\n-----------------'.format(len(warnings))
            )
        )
        for result in warnings:
            builder.add(ConsoleReport._format_result(result))

        successful = results.successful
        builder.add(
            Color.format(
                '\n[pass]Successful checks ({})[end]\n-----------------'.format(
                    len(successful)
                )
            )
        )
        for result in successful:
            builder.add(ConsoleReport._format_result(result))

        return builder.render()

    @staticmethod
    def get_summary(results):
        """Get a short summary of all results.

        :param CheckSuiteResults results: the object that contains the results
        """
        errors = results.errors
        warnings = results.warnings
        successful = results.successful

        builder = StringBuilder()

        builder.add('\n\n')
        builder.add('SUMMARY')
        builder.add('-------')
        builder.add(
            Color.format(
                '[fail]Failures ({})[end] - These need to be fixed'.format(len(errors))
            )
        )
        for result in errors:
            builder.add(
                Color.format('- [check][{}][end]'.format(result.config.check_type))
            )
        builder.add()

        builder.add(
            Color.format(
                '[warning]Warnings ({})[end] - '
                'Fixing these may not be applicable, please review them '
                'case by case'.format(len(warnings))
            )
        )
        for result in warnings:
            builder.add(
                Color.format('- [check][{}][end]'.format(result.config.check_type))
            )
        builder.add()

        builder.add(Color.format('[pass]Successful ({})[end]'.format(len(successful))))
        for result in successful:
            builder.add(
                Color.format('- [check][{}][end]'.format(result.config.check_type))
            )
        builder.add()

        return builder.render()

    class PRComments:
        """Provides messages to print to the console when working on PR comments."""

        @staticmethod
        def get_creation_pre_run():
            return 'Attempting to create new comment on pull request...'

        @staticmethod
        def get_creation_error(exception):
            return Color.format(
                '[error]Error while creating comment:[end]\n'
                '[fail]{}[end]\n'.format(exception)
            )

        @staticmethod
        def get_creation_success(comment_dict):
            return Color.format(
                '[success]Pull request comment successfully created '
                'at: [end]{}'.format(comment_dict['html_url'])
            )

        @staticmethod
        def get_deletion_pre_run():
            return 'Attempting to delete previous temcheck comment on pull request...'

        @staticmethod
        def get_deletion_error(exception):
            return Color.format(
                '[error]Error while deleting comment:[end]\n'
                '[fail]{}[end]\n'.format(exception)
            )

        @staticmethod
        def get_deletion_success():
            return Color.format(
                '[success]Successfully deleted previous comment on pull request[end]'
            )

        @staticmethod
        def get_deletion_failure():
            return Color.format('[success]No previous comment found to delete[end]')

    @staticmethod
    def _format_result(result):
        """Pretty-format the given result, adding colors and making it more readable.

        :param CheckResult result:
        """
        builder = StringBuilder()

        if result.success:
            builder.add(
                Color.format(
                    '[check][{}][end] ... [pass]{}[end]'.format(
                        result.config.check_type, result.status.upper()
                    )
                )
            )
        else:
            if result.status == STATUS_FAIL:
                builder.add(
                    Color.format(
                        '[check][{}][end] ... [fail]{}[end]'.format(
                            result.config.check_type, result.status.upper()
                        )
                    )
                )
            else:
                builder.add(
                    Color.format(
                        '[check][{}][end] ... [error]{}[end]'.format(
                            result.config.check_type, result.status.upper()
                        )
                    )
                )
            builder.add(
                Color.format('[h]Error code[end]: {}'.format(result.error_code))
            )
            builder.add(Color.format('[h]Details[end]:'))
            builder.add(pyaml.dump(result.details))
            builder.add()

        return builder.render()
