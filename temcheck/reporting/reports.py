import re

import pyaml
from temcheck.checks.results import STATUS_FAIL


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


class StringBuilder:
    """A utility class that can be used for the lazy creation of line-based
    report strings.
    """

    def __init__(self):
        self.strings = []

    def add(self, string=''):
        """Add a new line."""
        self.strings.append(string)

    def render(self):
        """Return a multi-line string with all the strings."""
        return '\n'.join(self.strings)


class ConsoleReport:
    """Creates reports to be used as console output when the checks run."""

    @staticmethod
    def get_pre_run_report(config, pr_url):
        """Print a message before running the checks.

        :param dict config: the configuration that will be used
        :param str pr_url: the URL of the pull request
        """
        check_types = config.keys()
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


class PRCommentReport:
    """Creates reports to be added as comments on the pull request
    that is being checked."""

    def __init__(self, results, details_url=None):
        """Constructor.

        :param CheckSuiteResults results: the object that contains the results
        :param str details_url: the URL to visit for more details about the results
        """
        self.results = results
        self.details_url = details_url

    def get_pre_run(self):
        """Return the text to print to the console before attempting
        to create the pull request comment.

        :rtype: str
        """
        return 'Attempting to create new comment on pull request...'

    def get_error(self, exception):
        """Return the text to print to the console if the creation
        of the pull request comment has failed.

        :rtype: str
        """
        return Color.format(
            '[error]Error while creating comment:[end]\n'
            '[fail]{}[end]\n'.format(exception)
        )

    def get_success(self, comment_dict):
        """Return the text to print to the console if the creation
        of the pull request comment was successful.

        :param dict comment_dict: a dictionary with information about
            the new comment that was created

        :rtype: str
        """
        return Color.format(
            '[success]Pull request comment successfully created '
            'at: [end]{}'.format(comment_dict['html_url'])
        )

    def get_summary(self):
        """Return a summary of the most important information about the results,
        to be used as a comment on the pull request.

        :rtype: str
        """
        errors = self.results.errors
        warnings = self.results.warnings
        successful = self.results.successful

        builder = StringBuilder()

        builder.add('# Pull Request Health Check')
        builder.add(
            'Checking if this PR follows the expected quality standards. '
            'Powered by [temcheck](https://www.github.com/transifex/temcheck).'
        )

        if len(errors) + len(warnings) == 0:
            builder.add('> All {} quality checks have passed!'.format(len(successful)))
        else:
            # Summary
            builder.add(
                '> Quality check revealed {} failures, {} warnings '
                'and {} successful checks.\n'.format(
                    len(errors), len(warnings), len(successful)
                )
            )

            # Failures
            builder.add(
                '**Failures ({})** - *These need to be fixed!*'.format(len(errors))
            )
            for result in errors:
                builder.add(PRCommentReport._format_result(result))
            builder.add()

            # Warnings
            builder.add(
                '**Warnings ({})** - '
                '*Fixing these may not be applicable, please review them '
                'case by case*'.format(len(warnings))
            )
            for result in warnings:
                builder.add(PRCommentReport._format_result(result))
            builder.add()

        # Successful checls
        builder.add('**Successful ({})** - *Good job!*'.format(len(successful)))
        for result in successful:
            builder.add('- **{}**'.format(result.config.check_type))
        builder.add()

        if self.details_url:
            builder.add('Visit the [details page]({}) for more information.'.format(
                self.details_url
            ))

        return builder.render()

    @staticmethod
    def _format_result(result):
        """Pretty-format the given result, adding markdown and making it more readable.

        :param CheckResult result:
        :return: a pretty-formatted string
        :rtype: str
        """
        # Get the message if it exists
        msg = result.details.get('message', '')

        # Enclose any occurrence of "...." inside ``, to make it more readable
        msg = re.sub('("[^\"]+")', '`\g<1>`', msg)

        # Add a new line before the "Explanation" part, which often appears
        # in messages
        msg = msg.replace('Explanation:', '\n  Explanation:')

        return '- **{}**\n  {}'.format(result.config.check_type, msg)
