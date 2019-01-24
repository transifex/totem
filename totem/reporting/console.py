"""Includes functionality for writing output on the console."""

import pyaml
from totem.checks.config import Config
from totem.checks.results import STATUS_FAIL, CheckResult, CheckSuiteResults
from totem.checks.suite import CheckSuite
from totem.reporting import StringBuilder


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
    def format(string: str) -> str:
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
    def print(string: str):
        """Print to the console with color support."""
        print(Color.format(string))


class BaseConsoleReport:
    """Creates reports to be used as console output when the checks run.

    A base class for classes that want to act as console output handlers.
    Subclasses need to override the `report_details` property,
    in order to return the proper configuration of the report.
    """

    def __init__(self, suite: CheckSuite):
        """Constructor.

        :param CheckSuite suite: the check suite that was executed
        """
        self.suite = suite

    @property
    def report_details(self) -> dict:
        # Subclasses need to override this, in order to return the proper
        # configuration, from the corresponding property of the `Config` class
        raise NotImplementedError()

    def get_pre_run_report(self, config: Config, pr_url: str) -> str:
        """Print a message before running the checks.

        :param Config config: the configuration that will be used
        :param str pr_url: the URL of the pull request
        """
        check_types = config.check_configs.keys()
        builder = StringBuilder()
        builder.add()
        builder.add(
            'About to check if the following PR follows the expected '
            'Quality Standards. Inspired by the Transifex Engineering Manifesto '
            '(https://tem.transifex.com/)'
        )
        builder.add('PR: {}'.format(pr_url))
        builder.add('\nWill run {} checks:'.format(len(check_types)))
        for check_type in check_types:
            builder.add(Color.format(' - [check][{}][end]'.format(check_type)))

        builder.add()
        return builder.render()

    def get_detailed_results(self, results: CheckSuiteResults) -> str:
        """Return a string with all results in detail.

        :param CheckSuiteResults results: the object that contains the results
        :return: the detailed string
        :rtype: str
        """
        builder = StringBuilder()

        comment_settings = self.report_details
        show_empty_sections = comment_settings.get('show_empty_sections', True)

        errors = results.errors
        if len(errors) or show_empty_sections:
            builder.add(
                Color.format(
                    '\n[error]Failures ({})[end]\n-----------------'.format(len(errors))
                )
            )
            for result in errors:
                builder.add(PRConsoleReport._format_result(result))

        warnings = results.warnings
        if len(warnings) or show_empty_sections:
            builder.add(
                Color.format(
                    '\n[warning]Warnings ({})[end]\n-----------------'.format(
                        len(warnings)
                    )
                )
            )
            for result in warnings:
                builder.add(PRConsoleReport._format_result(result))

        show_successful = comment_settings.get('show_successful', True)
        successful = results.successful
        if show_successful and (len(successful) or show_empty_sections):
            builder.add(
                Color.format(
                    '\n[pass]Successful checks ({})[end]\n-----------------'.format(
                        len(successful)
                    )
                )
            )
            for result in successful:
                builder.add(PRConsoleReport._format_result(result))

        return builder.render()

    def get_summary(self, results: CheckSuiteResults) -> str:
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

        comment_settings = self.report_details
        show_empty_sections = comment_settings.get('show_empty_sections', True)

        if len(errors) or show_empty_sections:
            builder.add(
                Color.format(
                    '[fail]Failures ({})[end] - These need to be fixed'.format(
                        len(errors)
                    )
                )
            )
            for result in errors:
                builder.add(
                    Color.format('- [check][{}][end]'.format(result.config.check_type))
                )
            builder.add()

        if len(warnings) or show_empty_sections:
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

        if len(successful) or show_empty_sections:
            builder.add(
                Color.format('[pass]Successful ({})[end]'.format(len(successful)))
            )
            for result in successful:
                builder.add(
                    Color.format('- [check][{}][end]'.format(result.config.check_type))
                )
            builder.add()

        return builder.render()

    class PRComments:
        """Provides messages to print to the console when working on PR comments."""

        @staticmethod
        def get_creation_pre_run() -> str:
            return 'Attempting to create new comment on pull request...'

        @staticmethod
        def get_creation_error(exception: Exception) -> str:
            return Color.format(
                '[error]Error while creating comment:[end]\n'
                '[fail]{}[end]\n'.format(exception)
            )

        @staticmethod
        def get_creation_success(comment_dict: dict) -> str:
            return Color.format(
                '[success]Pull request comment successfully created '
                'at: [end]{}'.format(comment_dict['html_url'])
            )

        @staticmethod
        def get_deletion_pre_run() -> str:
            return 'Attempting to delete previous totem comment on pull request...'

        @staticmethod
        def get_deletion_error(exception: Exception) -> str:
            return Color.format(
                '[error]Error while deleting comment:[end]\n'
                '[fail]{}[end]\n'.format(exception)
            )

        @staticmethod
        def get_deletion_success() -> str:
            return Color.format(
                '[success]Successfully deleted previous comment on pull request[end]'
            )

        @staticmethod
        def get_deletion_failure() -> str:
            return Color.format('[success]No previous comment found to delete[end]')

    @staticmethod
    def _format_result(result: CheckResult) -> str:
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


class PRConsoleReport(BaseConsoleReport):
    """Creates reports to be used as console output when the checks run
    on a pull request."""

    @property
    def report_details(self) -> dict:
        return self.suite.config.pr_console_report


class LocalConsoleReport(BaseConsoleReport):
    """Creates reports to be used as console output when the checks run
    on a local Git repository."""

    @property
    def report_details(self) -> dict:
        return self.suite.config.local_console_report
