import pytest
from totem.checks.checks import (
    BranchNameCheck,
    CommitMessagesCheck,
    PRBodyChecklistCheck,
    PRBodyExcludesCheck,
    PRBodyIncludesCheck,
    PRTitleCheck,
)
from totem.checks.config import CheckConfig
from totem.checks.results import (
    ERROR_FORBIDDEN_PR_BODY_TEXT,
    ERROR_INVALID_BRANCH_NAME,
    ERROR_INVALID_CONFIG,
    ERROR_INVALID_CONTENT,
    ERROR_INVALID_PR_TITLE,
    ERROR_MISSING_PR_BODY_TEXT,
    ERROR_UNFINISHED_CHECKLIST,
    STATUS_ERROR,
    STATUS_PASS,
)


class TestBranchNameCheck:
    """Tests the functionality of the BranchNameCheck class."""

    def test_default_config(self):
        check = BranchNameCheck(CheckConfig('branch_name', 'error'))
        result = check.run({'branch': 'some-thing-3-yo'})
        assert result.success is True

        result = check.run({'branch': 'invalid##name'})
        assert result.success is False
        assert result.error_code == ERROR_INVALID_BRANCH_NAME

    def test_custom_config(self):
        check = BranchNameCheck(
            CheckConfig('branch_name', 'error', pattern='^[abc99]+$')
        )
        result = check.run({'branch': 'ab9c9bb9ca9aa'})
        assert result.success is True

        result = check.run({'branch': 'ab9c9bb9-ca9aa'})
        assert result.success is False
        assert result.error_code == ERROR_INVALID_BRANCH_NAME

        result = check.run({'branch': 'db9c9bb9ca9aa'})
        assert result.success is False
        assert result.error_code == ERROR_INVALID_BRANCH_NAME

    def test_missing_branch_returns_success(self):
        check = BranchNameCheck(CheckConfig('branch_name', 'error'))
        result = check.run({'branch': None})
        assert result.status == STATUS_PASS
        assert result.details['message'] == (
            'Branch name not available, skipping branch name validation '
            '(could be a detached head)'
        )

    def test_empty_branch_returns_error(self):
        check = BranchNameCheck(CheckConfig('branch_name', 'error'))
        result = check.run({'branch': ''})
        assert result.status == STATUS_ERROR
        assert result.error_code == ERROR_INVALID_CONTENT
        assert result.details['message'] == 'Branch name not defined or empty'

    def test_missing_pattern_returns_error(self):
        for pattern in ('', None):
            check = BranchNameCheck(
                CheckConfig('branch_name', 'error', pattern=pattern)
            )
            result = check.run({'branch': 'something'})
            assert result.status == STATUS_ERROR
            assert result.error_code == ERROR_INVALID_CONFIG
            assert (
                result.details['message']
                == 'Branch name regex pattern not defined or empty'
            )


class TestPRTItle:
    """Tests the functionality of the PRTitleCheck class."""

    def test_default_config(self):
        check = PRTitleCheck(CheckConfig('whatever', 'error'))

        result = check.run({'title': 'Upper first letter - 3233'})
        assert result.success is True

        result = check.run({'title': 'ALL CAPS'})
        assert result.success is True

        result = check.run({'title': 'lowercase THEN CAPS'})
        assert result.success is False
        assert result.error_code == ERROR_INVALID_PR_TITLE

    def test_custom_config(self):
        check = PRTitleCheck(CheckConfig('title', 'error', pattern='^[abc99]+$'))

        result = check.run({'title': 'ab9c9bb9ca9aa'})
        assert result.success is True

        result = check.run({'title': 'ab9c9bb9-ca9aa'})
        assert result.success is False
        assert result.error_code == ERROR_INVALID_PR_TITLE

        result = check.run({'title': 'db9c9bb9ca9aa'})
        assert result.success is False
        assert result.error_code == ERROR_INVALID_PR_TITLE

    def test_missing_title_returns_error(self):
        check = PRTitleCheck(CheckConfig('title', 'error'))
        result = check.run({})  # no 'title' entry
        assert result.status == STATUS_ERROR
        assert result.error_code == ERROR_INVALID_CONTENT
        assert result.details['message'] == 'PR title not defined or empty'

    def test_missing_pattern_returns_error(self):
        check = PRTitleCheck(CheckConfig('title', 'error', pattern=''))
        result = check.run({'title': 'My title'})
        assert result.status == STATUS_ERROR
        assert result.error_code == ERROR_INVALID_CONFIG
        assert (
            result.details['message'] == 'PR title regex pattern not defined or empty'
        )


class TestPRBodyChecklist:
    """Tests the functionality of the PRBodyChecklist class."""

    def test_all(self):
        check = PRBodyChecklistCheck(CheckConfig('whatever', 'error'))

        result = check.run({'body': 'This is something. \n- [x]\n- [x]\n\n* [x]'})
        assert result.success is True

        result = check.run({'body': 'This is something. \n- []'})
        assert result.success is True

        result = check.run({'body': 'This is something. \n- [ ]\n- [x]\n\n* [x]'})
        assert result.success is False
        assert result.error_code == ERROR_UNFINISHED_CHECKLIST

        result = check.run({'body': 'This is something. \n- [x]\n- [x]\n\n* [ ]'})
        assert result.success is False
        assert result.error_code == ERROR_UNFINISHED_CHECKLIST


class TestPRBodyIncludes:
    """Tests the functionality of the PRBodyIncludesCheck class."""

    def test_all(self):
        check = PRBodyIncludesCheck(
            CheckConfig('whatever', 'error', patterns=['must-be', 'present'])
        )

        result = check.run({'body': 'Things must-be present'})
        assert result.success is True

        result = check.run({'body': 'A good present is a must-be'})
        assert result.success is True

        result = check.run({'body': 'present must be'})
        assert result.success is False
        assert result.error_code == ERROR_MISSING_PR_BODY_TEXT

        result = check.run({'body': 'must-be pres-ent'})
        assert result.success is False
        assert result.error_code == ERROR_MISSING_PR_BODY_TEXT

        result = check.run({'body': 'totally unrelated'})
        assert result.success is False
        assert result.error_code == ERROR_MISSING_PR_BODY_TEXT


class TestPRBodyExcludes:
    """Tests the functionality of the PRBodyExcludesCheck class."""

    def test_all(self):
        check = PRBodyExcludesCheck(
            CheckConfig('whatever', 'error', patterns=['forbidden', 'fruit'])
        )

        result = check.run({'body': 'Something about something else'})
        assert result.success is True

        result = check.run({'body': 'I love eating fruit'})
        assert result.success is False
        assert result.error_code == ERROR_FORBIDDEN_PR_BODY_TEXT

        result = check.run({'body': 'This is forbidden'})
        assert result.success is False
        assert result.error_code == ERROR_FORBIDDEN_PR_BODY_TEXT

        result = check.run({'body': 'Fruit is forbidden here'})
        assert result.success is False
        assert result.error_code == ERROR_FORBIDDEN_PR_BODY_TEXT


class TestCommitMessages:
    """Tests the functionality of the CommitMessagesCheck class."""

    @pytest.fixture
    def default_check(self):
        return CommitMessagesCheck(CheckConfig('whatever', 'error'))

    def test_default_pass(self, default_check):
        # All numbers within allowed thresholds
        result = default_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 20},
                        'message': 'This is a good commit message',
                        'sha': 'aa',
                        'url': '',
                    },
                    {
                        'stats': {'total': 4},
                        'message': 'This is also good\n\nBig description',
                        'sha': 'bb',
                        'url': '',
                    },
                ]
            }
        )
        assert result.success is True

    def test_default_at_threshold_pass(self, default_check):
        # All numbers exactly at the threshold value
        result = default_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 99},
                        'message': '{}\n\n{}'.format('X' * 50, 'k' * 72),
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )
        assert result.success is True

    def test_subject_too_long_fails(self, default_check):
        result = default_check.run(
            {
                'commits': [
                    {'stats': {'total': 4}, 'message': 'X' * 51, 'sha': 'aa', 'url': ''}
                ]
            }
        )
        assert result.success is False

    def test_subject_too_short_fails(self, default_check):
        result = default_check.run(
            {
                'commits': [
                    {'stats': {'total': 4}, 'message': 'X' * 5, 'sha': 'aa', 'url': ''}
                ]
            }
        )
        assert result.success is False

    def test_default_body_line_too_long_fails(self, default_check):
        result = default_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 4},
                        'message': '{}\n\n{}'.format('X' * 50, 'k' * 73),
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )
        assert result.success is False

    def test_default_too_many_changes_without_body_fails(self, default_check):
        result = default_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 101},
                        'message': '{}'.format('X' * 50),
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )
        assert result.success is False

    def test_default_many_changes_with_body_pass(self, default_check):
        result = default_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 101},
                        'message': '{}\n\n{}'.format('X' * 50, 'YYYY'),
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )
        assert result.success is True

    @pytest.fixture
    def custom_check(self):
        options = {
            'subject': {'min_length': 2, 'max_length': 5, 'pattern': '^[a-z]+$'},
            'body': {
                'max_line_length': 10,
                'smart_require': {'min_changes': 5, 'min_body_lines': 3},
            },
        }
        return CommitMessagesCheck(CheckConfig('whatever', 'error', **options))

    def test_custom_pass(self, custom_check):
        # All numbers within allowed thresholds
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 20},
                        'message': 'tests\n\nabcd\nabcde\n1010',
                        'sha': 'bb',
                        'url': '',
                    },
                    {
                        'stats': {'total': 4},
                        'message': 'done\n\n123456789\n12345\n6789',
                        'sha': 'bb',
                        'url': '',
                    },
                ]
            }
        )
        assert result.success is True

    def test_custom_at_threshold_pass(self, custom_check):
        # All numbers exactly at the threshold value
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 99},
                        'message': '{}\n\n{}'.format('x' * 5, 'Aaaa\nBbbb\nCccc'),
                        'sha': 'aa',
                        'url': '',
                    },
                    {
                        'stats': {'total': 2},
                        'message': '{}\n\n{}'.format('x' * 2, 'Aaaa\nBbbb\nCccc'),
                        'sha': 'aa',
                        'url': '',
                    },
                ]
            }
        )
        assert result.success is True

    def test_custom_subject_too_long_fails(self, custom_check):
        result = custom_check.run(
            {
                'commits': [
                    {'stats': {'total': 4}, 'message': 'X' * 2, 'sha': 'aa', 'url': ''},
                    {'stats': {'total': 3}, 'message': 'X' * 6, 'sha': 'aa', 'url': ''},
                ]
            }
        )
        assert result.success is False

    def test_custom_body_line_too_long_fails(self, custom_check):
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 4},
                        'message': '{}\n\n{}'.format('X' * 5, 'k' * 11),
                        'sha': 'aa',
                        'url': '',
                    },
                    {
                        'stats': {'total': 2},
                        'message': '{}\n\n{}'.format('X' * 3, 'k' * 6),
                        'sha': 'aa',
                        'url': '',
                    },
                ]
            }
        )
        assert result.success is False

    def test_custom_too_many_changes_without_body_fails(self, custom_check):
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 11},
                        'message': '{}'.format('X' * 5),
                        'sha': 'aa',
                        'url': '',
                    },
                    {
                        'stats': {'total': 10},
                        'message': '{}'.format('X' * 5),
                        'sha': 'aa',
                        'url': '',
                    },
                ]
            }
        )
        assert result.success is False

    def test_custom_many_changes_with_body_pass(self, custom_check):
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 11},
                        'message': '{}\n\n{}'.format('x' * 5, 'Aaaa\nBbbb\nCccc'),
                        'sha': 'aa',
                        'url': '',
                    },
                    {'stats': {'total': 4}, 'message': 'x' * 5, 'sha': 'aa', 'url': ''},
                ]
            }
        )
        assert result.success is True

    @pytest.fixture()
    def custom_config(self):
        return {
            'subject': {'min_length': 5, 'max_length': 10, 'pattern': '^[a-z]+$'},
            'body': {
                'max_line_length': 10,
                'smart_require': {'min_changes': 5, 'min_body_lines': 3},
            },
        }

    def test_no_subject_min_length_option_ignored(self, custom_config):
        """If the config does not include a subject.min_length option,
        no lower limit should be rejected."""
        del custom_config['subject']['min_length']
        check = CommitMessagesCheck(CheckConfig('whatever', 'error', **custom_config))
        result = check.run(
            {
                'commits': [
                    {'stats': {'total': 2}, 'message': 'x' * 1, 'sha': 'aa', 'url': ''}
                ]
            }
        )
        assert result.success is True

    def test_no_subject_max_length_option_ignored(self, custom_config):
        """If the config does not include a subject.max_length option,
        no upper limit should be rejected."""
        del custom_config['subject']['max_length']
        check = CommitMessagesCheck(CheckConfig('whatever', 'error', **custom_config))
        result = check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 2},
                        'message': 'x' * 1000,
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )
        assert result.success is True

    def test_no_subject_pattern_option_ignored(self, custom_config):
        """If the config does not include a subject.pattern option,
        no pattern should be rejected."""
        del custom_config['subject']['pattern']
        check = CommitMessagesCheck(CheckConfig('whatever', 'error', **custom_config))
        result = check.run(
            {
                'commits': [
                    {'stats': {'total': 2}, 'message': 'A82%@$', 'sha': 'aa', 'url': ''}
                ]
            }
        )
        assert result.success is True

    def test_no_body_max_line_length_option_ignored(self, custom_config):
        """If the config does not include a body.max_line_length option,
        no upper limit should be rejected."""
        del custom_config['body']['max_line_length']
        check = CommitMessagesCheck(CheckConfig('whatever', 'error', **custom_config))
        result = check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 2},
                        'message': 'xxxxx\n\n{}'.format('A' * 1000),
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )
        assert result.success is True

    def test_no_body_smart_require_min_body_lines_option_ignored(self, custom_config):
        """If the config does not include a body.smart_require.min_changes option,
        no smart check should be performed."""
        del custom_config['body']['smart_require']['min_changes']
        check = CommitMessagesCheck(CheckConfig('whatever', 'error', **custom_config))
        result = check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 2000},
                        'message': 'xxxxx',
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )
        assert result.success is True

    def test_missing_key_from_config_fails_with_error(self, custom_config):
        """If the content of a commit does not include required keys,
        the check should fail with an error."""
        del custom_config['subject']
        check = CommitMessagesCheck(CheckConfig('whatever', 'error', **custom_config))
        result = check.run({'commits': [{'message': 'xxxxx', 'sha': 'aa', 'url': ''}]})
        assert result.success is False
        assert result.status is 'error'
        assert result.error_code is 'invalid_content'
        assert "Missing key: 'stats'" in result.details['message']
