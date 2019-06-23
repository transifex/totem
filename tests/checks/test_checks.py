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
        result = check.run({'branch': 'some-thing-3-yo'})[0]
        assert result.success is True

        result = check.run({'branch': 'invalid##name'})[0]
        assert result.success is False
        assert result.error_code == ERROR_INVALID_BRANCH_NAME

    def test_custom_config(self):
        check = BranchNameCheck(
            CheckConfig('branch_name', 'error', pattern='^[abc99]+$')
        )
        result = check.run({'branch': 'ab9c9bb9ca9aa'})[0]
        assert result.success is True

        result = check.run({'branch': 'ab9c9bb9-ca9aa'})[0]
        assert result.success is False
        assert result.error_code == ERROR_INVALID_BRANCH_NAME

        result = check.run({'branch': 'db9c9bb9ca9aa'})[0]
        assert result.success is False
        assert result.error_code == ERROR_INVALID_BRANCH_NAME

    def test_missing_branch_returns_success(self):
        check = BranchNameCheck(CheckConfig('branch_name', 'error'))
        result = check.run({'branch': None})[0]
        assert result.status == STATUS_PASS
        assert result.details['message'] == (
            'Branch name not available, skipping branch name validation '
            '(could be a detached head)'
        )

    def test_empty_branch_returns_error(self):
        check = BranchNameCheck(CheckConfig('branch_name', 'error'))
        result = check.run({'branch': ''})[0]
        assert result.status == STATUS_ERROR
        assert result.error_code == ERROR_INVALID_CONTENT
        assert result.details['message'] == 'Branch name not defined or empty'

    def test_missing_pattern_returns_error(self):
        for pattern in ('', None):
            check = BranchNameCheck(
                CheckConfig('branch_name', 'error', pattern=pattern)
            )
            result = check.run({'branch': 'something'})[0]
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

        result = check.run({'title': 'Upper first letter - 3233'})[0]
        assert result.success is True

        result = check.run({'title': 'ALL CAPS'})[0]
        assert result.success is True

        result = check.run({'title': 'lowercase THEN CAPS'})[0]
        assert result.success is False
        assert result.error_code == ERROR_INVALID_PR_TITLE

    def test_custom_config(self):
        check = PRTitleCheck(CheckConfig('title', 'error', pattern='^[abc99]+$'))

        result = check.run({'title': 'ab9c9bb9ca9aa'})[0]
        assert result.success is True

        result = check.run({'title': 'ab9c9bb9-ca9aa'})[0]
        assert result.success is False
        assert result.error_code == ERROR_INVALID_PR_TITLE

        result = check.run({'title': 'db9c9bb9ca9aa'})[0]
        assert result.success is False
        assert result.error_code == ERROR_INVALID_PR_TITLE

    def test_missing_title_returns_error(self):
        check = PRTitleCheck(CheckConfig('title', 'error'))
        result = check.run({})[0]  # no 'title' entry
        assert result.status == STATUS_ERROR
        assert result.error_code == ERROR_INVALID_CONTENT
        assert result.details['message'] == 'PR title not defined or empty'

    def test_missing_pattern_returns_error(self):
        check = PRTitleCheck(CheckConfig('title', 'error', pattern=''))
        result = check.run({'title': 'My title'})[0]
        assert result.status == STATUS_ERROR
        assert result.error_code == ERROR_INVALID_CONFIG
        assert (
            result.details['message'] == 'PR title regex pattern not defined or empty'
        )


class TestPRBodyChecklist:
    """Tests the functionality of the PRBodyChecklist class."""

    def test_all(self):
        check = PRBodyChecklistCheck(CheckConfig('whatever', 'error'))

        result = check.run({'body': 'This is something. \n- [x]\n- [x]\n\n* [x]'})[0]
        assert result.success is True

        result = check.run({'body': 'This is something. \n- []'})[0]
        assert result.success is True

        result = check.run({'body': 'This is something. \n- [ ]\n- [x]\n\n* [x]'})[0]
        assert result.success is False
        assert result.error_code == ERROR_UNFINISHED_CHECKLIST

        result = check.run({'body': 'This is something. \n- [x]\n- [x]\n\n* [ ]'})[0]
        assert result.success is False
        assert result.error_code == ERROR_UNFINISHED_CHECKLIST


class TestPRBodyIncludes:
    """Tests the functionality of the PRBodyIncludesCheck class."""

    def test_all(self):
        check = PRBodyIncludesCheck(
            CheckConfig('whatever', 'error', patterns=['must-be', 'present'])
        )

        result = check.run({'body': 'Things must-be present'})[0]
        assert result.success is True

        result = check.run({'body': 'A good present is a must-be'})[0]
        assert result.success is True

        result = check.run({'body': 'present must be'})[0]
        assert result.success is False
        assert result.error_code == ERROR_MISSING_PR_BODY_TEXT

        result = check.run({'body': 'must-be pres-ent'})[0]
        assert result.success is False
        assert result.error_code == ERROR_MISSING_PR_BODY_TEXT

        result = check.run({'body': 'totally unrelated'})[0]
        assert result.success is False
        assert result.error_code == ERROR_MISSING_PR_BODY_TEXT


class TestPRBodyExcludes:
    """Tests the functionality of the PRBodyExcludesCheck class."""

    def test_all(self):
        check = PRBodyExcludesCheck(
            CheckConfig('whatever', 'error', patterns=['forbidden', 'fruit'])
        )

        result = check.run({'body': 'Something about something else'})[0]
        assert result.success is True

        result = check.run({'body': 'I love eating fruit'})[0]
        assert result.success is False
        assert result.error_code == ERROR_FORBIDDEN_PR_BODY_TEXT

        result = check.run({'body': 'This is forbidden'})[0]
        assert result.success is False
        assert result.error_code == ERROR_FORBIDDEN_PR_BODY_TEXT

        result = check.run({'body': 'Fruit is forbidden here'})[0]
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
        )[0]
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
        )[0]
        assert result.success is True

    def test_subject_too_long_fails(self, default_check):
        result = default_check.run(
            {
                'commits': [
                    {'stats': {'total': 4}, 'message': 'X' * 51, 'sha': 'aa', 'url': ''}
                ]
            }
        )[0]
        assert result.success is False

    def test_subject_too_short_fails(self, default_check):
        result = default_check.run(
            {
                'commits': [
                    {'stats': {'total': 4}, 'message': 'X' * 5, 'sha': 'aa', 'url': ''}
                ]
            }
        )[0]
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
        )[0]
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
        )[0]
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
        )[0]
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
        )[0]
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
        )[0]
        assert result.success is True

    def test_custom_subject_too_long_fails(self, custom_check):
        results = custom_check.run(
            {
                'commits': [
                    {'stats': {'total': 4}, 'message': 'X' * 2, 'sha': 'aa', 'url': ''},
                    {'stats': {'total': 3}, 'message': 'X' * 6, 'sha': 'aa', 'url': ''},
                ]
            }
        )
        assert results[0].success is False
        assert 'error_subject_pattern' in results[0].details['errors'][0]
        assert len(results[0].details['errors']) == 1

        assert results[1].success is False
        assert 'error_subject_pattern' in results[1].details['errors'][0]
        assert 'error_subject_length' in results[1].details['errors'][0]
        assert len(results[1].details['errors']) == 1

    def test_custom_body_line_too_long_fails(self, custom_check):
        results = custom_check.run(
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
        assert results[0].success is False
        assert 'error_subject_pattern' in results[0].details['errors'][0]
        assert 'error_body_length' in results[0].details['errors'][0]
        assert len(results[0].details['errors']) == 1

        assert results[1].success is False
        assert 'error_subject_pattern' in results[1].details['errors'][0]
        assert len(results[1].details['errors']) == 1

    def test_custom_too_many_changes_without_body_fails(self, custom_check):
        results = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 11},
                        'message': 'subject\n\nsomething\nhahaha',
                        'sha': 'aa',
                        'url': '',
                    },
                    {
                        'stats': {'total': 3},
                        'message': 'subj\n\nLine 1\nLine 2\nLine 3',
                        'sha': 'aa',
                        'url': '',
                    },
                ]
            }
        )
        assert results[0].success is False
        assert 'error_smart_body_size' in results[0].details['errors'][0]
        assert len(results[0].details['errors']) == 1

        assert len(results) == 1

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
        )[0]
        assert result.success is True
        assert 'errors' not in result.details

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
        )[0]
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
        )[0]
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
        )[0]
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
        )[0]
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
        )[0]
        assert result.success is True

    def test_missing_key_from_config_fails_with_error(self, custom_config):
        """If the content of a commit does not include required keys,
        the check should fail with an error."""
        del custom_config['subject']
        check = CommitMessagesCheck(CheckConfig('whatever', 'error', **custom_config))
        result = check.run({'commits': [{'message': 'xxxxx', 'sha': 'aa', 'url': ''}]})[
            0
        ]

        assert result.success is False
        assert result.status is 'error'
        assert result.error_code is 'invalid_content'
        assert "Missing key: 'stats'" in result.details['message']

    def test_url_in_message_ignores_max_length(self, custom_check):
        """Test that body lines with URLs ignore the max length limit."""
        urls = (
            'http://www.example.com',
            'https://www.example.com',
            'ftp://www.example.com',
        )
        for url in urls:
            result = custom_check.run(
                {
                    'commits': [
                        {
                            'stats': {'total': 2},
                            'message': 'subj\n\nThis is a long url: {}'.format(url),
                            'sha': 'aa',
                            'url': '',
                        },
                        {
                            'stats': {'total': 2},
                            'message': 'x' * 5,
                            'sha': 'aa',
                            'url': '',
                        },
                    ]
                }
            )[0]
            assert result.success is True
            assert 'errors' not in result.details

    def test_invalid_url_formats_in_message_respect_max_length(self, custom_check):
        """Test that invalid URLs, or those that do not follow a specific format
        are not treated as a special case."""
        urls = ('www.example.com', 'invalid:/www.example.com')
        for url in urls:
            result = custom_check.run(
                {
                    'commits': [
                        {
                            'stats': {'total': 2},
                            'message': 'subj\n\nThis is a long url: {}'.format(url),
                            'sha': 'aa',
                            'url': '',
                        },
                        {
                            'stats': {'total': 2},
                            'message': 'x' * 5,
                            'sha': 'aa',
                            'url': '',
                        },
                    ]
                }
            )[0]
            assert result.success is False
            assert 'error_body_length' in result.details['errors'][0]
            assert len(result.details['errors']) == 1

    def test_global_ignore_flag_in_body_ignores_all_errors(self, custom_check):
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 2},
                        'message': 'SUBJECT IS CAPS AND TOO LONG\n\n[!totem]',
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )[0]
        assert result.success is True
        assert 'errors' not in result.details

    def test_global_ignore_flag_in_subject_does_nothing(self, custom_check):
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 2},
                        'message': 'SUBJECT IS CAPS AND TOO LONG[!totem]',
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )[0]
        assert result.success is False
        assert 'error_subject_length' in result.details['errors'][0]
        assert len(result.details['errors']) == 1

    def test_line_ignore_flag_ignores_line_errors(self, custom_check):
        result = custom_check.run(
            {
                'commits': [
                    {
                        'stats': {'total': 2},
                        'message': 'subj\n\nThis is a very long line indeed!! #!totem',
                        'sha': 'aa',
                        'url': '',
                    }
                ]
            }
        )[0]
        assert result.success is True
        assert 'errors' not in result.details
