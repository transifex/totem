import re

from temcheck.checks.core import Check
from temcheck.checks.results import (
    ERROR_FORBIDDEN_PR_BODY_TEXT,
    ERROR_INVALID_BRANCH_NAME,
    ERROR_INVALID_COMMIT_MESSAGE_FORMAT,
    ERROR_INVALID_CONFIG,
    ERROR_INVALID_CONTENT,
    ERROR_INVALID_PR_TITLE,
    ERROR_MISSING_PR_BODY_TEXT,
    ERROR_UNFINISHED_CHECKLIST,
)

TYPE_BRANCH_NAME = 'branch_name'
TYPE_PR_TITLE = 'pr_title'
TYPE_PR_BODY_CHECKLIST = 'pr_body_checklist'
TYPE_PR_BODY_INCLUDES = 'pr_body_includes'
TYPE_PR_BODY_EXCLUDES = 'pr_body_excludes'
TYPE_COMMIT_MESSAGE = 'commit_message'


class BranchNameCheck(Check):
    """Checks whether or not a branch name follows a certain format."""

    def run(self, content):
        """Check if a branch name follows a certain format.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        pattern = self._from_config('pattern')
        branch_name = content.get('branch')

        if not branch_name:
            return self._get_error(
                ERROR_INVALID_CONTENT, message='Branch name not defined or empty'
            )

        if not pattern:
            return self._get_error(
                ERROR_INVALID_CONFIG,
                message='Branch name regex pattern not defined or empty',
            )

        success = re.search(pattern, branch_name) is not None
        if not success:
            msg = (
                'Branch name "{}" doesn\'t match pattern: "{}". '
                'Explanation: {}'.format(
                    branch_name, pattern, self._from_config('pattern_descr')
                )
            )
            return self._get_failure(ERROR_INVALID_BRANCH_NAME, message=msg)

        return self._get_success()

    def _default_config(self, name):
        if name == 'pattern':
            return '^[\w\d]\-]+$'
        elif name == 'pattern_descr':
            return (
                'Branch name must only include lowercase characters, numbers and dashes'
            )


class PRTitleCheck(Check):
    """Checks whether or not the title of a PR follows a certain format."""

    def run(self, content):
        """Check if a PR title follows a certain format.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        pattern = self._from_config('pattern')
        title = content.get('title')

        if not title:
            return self._get_error(
                ERROR_INVALID_CONTENT, message='PR title not defined or empty'
            )

        if not pattern:
            return self._get_error(
                ERROR_INVALID_CONFIG,
                message='PR title regex pattern not defined or empty',
            )

        success = re.search(pattern, title) is not None
        if not success:
            msg = 'PR title "{}" doesn\'t match pattern: "{}". Explanation: {}'.format(
                title, pattern, self._from_config('pattern_descr')
            )
            return self._get_failure(ERROR_INVALID_PR_TITLE, message=msg)

        return self._get_success()

    def _default_config(self, name):
        if name == 'pattern':
            return '^[A-Z].+$'
        elif name == 'pattern_descr':
            return 'PR title must start with an uppercase character'


class PRBodyChecklistCheck(Check):
    """Checks whether or not there are unchecked checklist items in the body
    of a pull request.

    Many TEM templates include a checklist that the reviewer has to complete
    before the PR can be merged. Also, some developers use checklists as a TODO
    before merging a PR.

    This check makes sure that no item in a checklist is left uncheck, because
    this would mean that something is not complete yet.

    It uses markdown syntax.
    """

    def run(self, content):
        """Check if the body of a PR contains unchecked items.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        body = content.get('body')

        matches = re.findall('[-*] \[ \]', body)
        if matches:
            return self._get_failure(
                ERROR_UNFINISHED_CHECKLIST,
                message='Found {} unfinished checklist items'.format(len(matches)),
            )

        return self._get_success()


class PRBodyIncludesCheck(Check):
    """Makes sure that the PR body includes certain required strings.

    This is useful in cases there are things that should always
    be present inside a pull request body.

    This check tests again multiple regex patterns. It always checks them all
    and the result it returns includes all the ones that failed.
    """

    def run(self, content):
        """Check if the body of a PR contains specific text.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed, successful if
            all of the strings are included, failed otherwise
        :rtype: CheckResult
        """
        body = content.get('body')

        patterns = self._from_config('patterns', [])
        failed_items = []
        for pattern in patterns:
            success = re.search(pattern, body, re.MULTILINE) is not None
            if not success:
                failed_items.append(pattern)

        if failed_items:
            return self._get_failure(
                ERROR_MISSING_PR_BODY_TEXT,
                message='Required strings in PR body are missing: {}'.format(
                    ', '.join(['"{}"'.format(x) for x in failed_items])
                ),
            )

        return self._get_success()


class PRBodyExcludesCheck(Check):
    """Makes sure that the PR body does not include certain strings.

    This is useful in cases there are "forbidden" things, that shouldn't
    be present inside a pull request body.

    This check tests again multiple regex patterns. It always checks them all
    and the result it returns includes all the ones that failed.
    """

    def run(self, content):
        """Check if the body of a PR contains specific text.

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed, successful if
            none of the strings are included, failed otherwise
        :rtype: CheckResult
        """
        body = content.get('body')

        patterns = self._from_config('patterns', [])
        failed_items = []
        for pattern in patterns:
            success = re.search(pattern, body, re.MULTILINE) is None
            if not success:
                failed_items.append(pattern)

        if failed_items:
            return self._get_failure(
                ERROR_FORBIDDEN_PR_BODY_TEXT,
                message='Forbidden strings found in PR body: {}'.format(
                    ', '.join(['"{}"'.format(x) for x in failed_items])
                ),
            )

        return self._get_success()


class CommitMessagesCheck(Check):
    """Makes sure that all commit messages of a PR are properly formatted."""

    def run(self, content):
        """Check if the commit messages of a PR are properly formatted.

        The content of `commits` should have the following format:
        'commits': [
            {'message': <message>, 'sha': <sha>, 'url': <url>},
            ...,
            {'message': <message>, 'sha': <sha>, 'url': <url>},
        ],

        :param dict content: contains parameters with the actual content to check
        :return: the result of the check that was performed
        :rtype: CheckResult
        """
        commits = content.get('commits')

        subject_config = self._from_config('subject')
        if not subject_config:
            return self._get_error(
                ERROR_INVALID_CONFIG,
                message='Configuration for commit checks should include '
                'a "subject" key',
            )
        body_config = self._from_config('body')
        if not body_config:
            return self._get_error(
                ERROR_INVALID_CONFIG,
                message='Configuration for commit checks should include '
                'a "body_config" key',
            )

        # Catch exceptions due to invalid format of the content
        # In the future, we could alternatively validate the content via Schema
        try:
            failed_items = []
            for index, commit in enumerate(commits):
                errors = self._check_message(commit)
                success = errors is None
                if not success:
                    errors['commit_order'] = index + 1
                    failed_items.append(errors)

        except KeyError:
            return self._get_error(
                ERROR_INVALID_CONTENT,
                message='Content for commit checks has invalid structure',
            )

        if failed_items:
            return self._get_failure(
                ERROR_INVALID_COMMIT_MESSAGE_FORMAT,
                message='Found {} commit message(s) that do not follow '
                'the correct format'.format(len(failed_items)),
                errors=failed_items,
            )

        return self._get_success()

    def _check_message(self, commit):
        """Check the given commit message against the rules defined in the config
        and return the results.

        :param dict commit: a dictionary containing information about a commit,
            formatted as: {'message': <message>, 'sha': <sha>, 'url': <url>}
        :return: a dictionary with all errors found or None if no error was found,
            formatted as:
            {
              'subject_length': <msg>,
              'subject_pattern': <msg>,
              'body_length': <msg>,
              'sha': <sha>,
              'url': <url>,
            }
        :rtype: dict
        """
        message = commit['message']
        lines = [line.strip() for line in message.splitlines()]

        # Find the subject and the body of the commit message
        # The subject is the part of the message until a newline is found
        # or the string ends (if no newline exists)
        # The body is the rest. If there is no newline in the message,
        # then the body is considered to be empty
        subject = message
        body_lines = []
        if '' in lines:
            separator_index = lines.index('')
            subject = '\n'.join(lines[0:separator_index])
            body_lines = lines[separator_index:]

        # Check subject
        subject_config = self._from_config('subject')
        max_length = subject_config.get('max_length', 0)
        subject_pattern = subject_config.get('pattern')

        subject_length_ok = len(subject) <= max_length if max_length else True
        subject_pattern_ok = (
            re.search(subject_pattern, subject) is not None if subject_pattern else True
        )

        # Check body
        body_config = self._from_config('body')
        max_line_length = body_config.get('max_line_length', 0)
        body_length_ok = all([len(x) <= max_line_length for x in body_lines])

        if all([subject_length_ok, subject_pattern_ok, body_length_ok]):
            return None

        errors = {'sha': commit['sha'], 'url': commit['url']}
        if not subject_length_ok:
            errors[
                'subject_length'
            ] = 'Subject has {} characters but the limit is {}'.format(
                len(subject), max_length
            )
        if not subject_pattern_ok:
            errors[
                'subject_pattern'
            ] = 'Subject does not follow pattern: {}. Explanation: {}'.format(
                subject_pattern, subject_config.get('pattern_descr', 'None')
            )
        if not body_length_ok:
            errors[
                'body_length'
            ] = 'One or more lines of the body are longer than {} characters'.format(
                max_line_length
            )

        return errors

    def _default_config(self, name):
        if name == 'subject':
            return {
                'max_length': 50,
                'pattern': '^[A-Z].+(?<!\.)$',
                'pattern_descr': 'Commit message subject must start with '
                'a capital letter and not finish with a dot',
            }
        elif name == 'body':
            return {'max_line_length': 72}
