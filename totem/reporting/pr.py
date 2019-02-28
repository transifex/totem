import re

import pyaml
from totem.checks.results import CheckResult
from totem.checks.suite import CheckSuite
from totem.reporting import StringBuilder


class PRCommentReport:
    """Creates reports to be added as comments on the pull request
    that is being checked."""

    TITLE = '# Totem Health Check'

    def __init__(self, suite: CheckSuite, details_url: str = None):
        """Constructor.

        :param CheckSuite suite: the check suite that was executed
        :param str details_url: the URL to visit for more details about the results
        """
        self.suite = suite
        self.details_url = details_url

    def get_summary(self) -> str:
        """Return a summary of the most important information about the results,
        to be used as a comment on the pull request.

        :rtype: str
        """
        errors = self.suite.results.errors
        warnings = self.suite.results.warnings
        successful = self.suite.results.successful
        total = len(errors) + len(warnings) + len(successful)

        builder = StringBuilder()

        builder.add(PRCommentReport.TITLE)
        builder.add(
            'Checking if this PR follows the expected quality standards. '
            'Powered by [totem](https://www.github.com/transifex/totem).\n'
        )

        comment_settings = self.suite.config.pr_comment_report
        show_empty_sections = comment_settings.get('show_empty_sections', True)

        if total == 0:
            builder.add(
                ':interrobang: No quality checks found to run. '
                'Please update your config!'
            )
        elif len(errors) + len(warnings) == 0:
            builder.add(
                ':white_check_mark: All {} quality checks have passed! '
                'Good job!'.format(len(successful))
            )
        else:
            # Summary
            total_errors = len(errors)
            total_warnings = len(warnings)
            total_successful = len(successful)
            builder.add(
                'failures | warnings | successful\n'
                '----------- | ------------- | -------------\n'
                '|{} | {} | {}\n'.format(
                    total_errors if total_errors else '-',
                    total_warnings if total_warnings else '-',
                    total_successful if total_successful else '-',
                )
            )

            # Failures
            if len(errors) or show_empty_sections:
                builder.add(
                    ':bangbang: **Failures ({})** '
                    '- *These need to be fixed!*'.format(len(errors))
                )
                for result in errors:
                    builder.add(self._format_result(result))
                builder.add()

            # Warnings
            if len(warnings) or show_empty_sections:
                builder.add(
                    ':eight_pointed_black_star: **Warnings ({})** - '
                    '*Fixing these may not be applicable, please review them '
                    'case by case*'.format(len(warnings))
                )
                for result in warnings:
                    builder.add(self._format_result(result))
                builder.add()

        # Successful checks
        show_successful = self.suite.config.pr_comment_report.get(
            'show_successful', True
        )
        if show_successful and (len(successful) or show_empty_sections):
            builder.add(
                ':white_check_mark: **Successful ({})** '
                '- *Good job on these!*'.format(len(successful))
            )
            for result in successful:
                builder.add('- **{}**'.format(result.config.check_type))
            builder.add()

        if self.details_url:
            builder.add(
                '\nVisit the [details page]({}) for more information.'.format(
                    self.details_url
                )
            )

        return builder.render()

    def _format_result(self, result: CheckResult) -> str:
        """Pretty-format the given result, adding markdown and making it more readable.

        :param CheckResult result:
        :return: a pretty-formatted string
        :rtype: str
        """
        # The check type will always be shown
        # The settings will tell us if we should show the message or not (on its own)
        msg = None
        show_message = self.suite.config.pr_comment_report.get('show_message', True)
        if show_message:
            # Get the message if it exists
            msg = result.details.get('message', '')

            # Enclose any occurrence of "...." inside ``, to make it more readable
            msg = PRCommentReport._increase_readability(msg)

            # Add a new line before the "Explanation" part, which often appears
            # in messages
            msg = msg.replace('Explanation:', '\n  Explanation:')

        # The settings will tell us if we should show all details or not
        # The message is part of the details, so if it's already being shown
        # do not show it again
        details = None
        if self.suite.config.pr_comment_report.get('show_details', False):
            result_details = dict(result.details)
            if show_message:
                del result_details['message']
            if not result_details:
                details = None
            else:
                details = PRCommentReport._increase_readability(
                    pyaml.dump(result_details)
                )

        msg = '\n  {}'.format(msg) if msg else ''
        details = '\n  {}'.format(details) if details else ''
        return '- **{check_type}**{msg}{details}'.format(
            check_type=result.config.check_type, msg=msg, details=details
        )

    @staticmethod
    def _increase_readability(string: str) -> str:
        """Enclose any occurrence of "...." inside ``, to make it more readable."""
        return re.sub('("[^\"]+")', '`\g<1>`', string)
