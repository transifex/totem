from totem.checks.checks import PR_TYPES_CHECKS
from totem.checks.config import Config, ConfigFactory


class TestConfig:
    """Test the Config class."""

    def test_constructor(self):
        settings = {'doesnt': 'matter'}
        check_configs = {'doesnt': 'matter'}
        config = Config(settings, check_configs)

        assert config.settings == settings
        assert config.check_configs == check_configs

    def test_default_pr_comment_report_property(self):
        config = Config({}, {})
        assert config.pr_comment_report == {
            'enabled': True,
            'show_message': True,
            'show_empty_sections': False,
            'show_errors': False,
        }

    def test_default_pr_console_report_property(self):
        config = Config({}, {})
        assert config.pr_console_report == {
            'show_message': True,
            'show_empty_sections': True,
            'show_details': True,
            'show_successful': True,
        }

    def test_default_local_console_report_property(self):
        config = Config({}, {})
        assert config.local_console_report == {
            'show_message': True,
            'show_empty_sections': False,
            'show_details': True,
            'show_successful': False,
        }

    def test_pr_comment_property(self):
        settings = {'pr_comment_report': {'doesnt': 'matter'}}
        config = Config(settings, {})
        assert config.pr_comment_report == settings['pr_comment_report']


class TestConfigFactory:
    """Tests the functionality of the ConfigFactory class."""

    def test_create(self):
        """Test the `.create()` method.

        It simply checks that all data is passed into the created Config object.
        Note that no validation is performed by the factory on the data,
        so the data can be anything.
        """
        config_dict = {
            'settings': {'a': 1, 'b': 2},
            'checks': {
                'branch_name': {
                    'pattern': '^TX-[0-9]+\-[\w\d\-]+$',
                    'failure_level': 'warning',
                },
                'doesnt_matter': {'failure_level': 'error'},
            },
        }
        config = ConfigFactory.create(config_dict)

        # Test settings
        assert config.settings == {'a': 1, 'b': 2}

        # Test checks
        check_configs = config.check_configs

        branch_name = check_configs['branch_name']
        assert branch_name.check_type == 'branch_name'
        assert branch_name.failure_level == 'warning'
        assert branch_name.options == {'pattern': '^TX-[0-9]+\-[\w\d\-]+$'}

        doesnt_matter = check_configs['doesnt_matter']
        assert doesnt_matter.check_type == 'doesnt_matter'
        assert doesnt_matter.failure_level == 'error'
        assert doesnt_matter.options == {}

    def test_create_without_pr(self):
        """Test the `.create()` method with `include_pr=False`.

        It simply checks that all data is passed into the created Config object
        and that all PR-specific checks are ignored.

        Note that no other validation is performed by the factory on the data,
        so the data can be anything.
        """
        config_dict = {
            'settings': {'a': 1, 'b': 2},
            'checks': {
                'branch_name': {
                    'pattern': '^TX-[0-9]+\-[\w\d\-]+$',
                    'failure_level': 'warning',
                },
                'pr_title': {'some': 'thing'},
                'pr_body_checklist': {'some': 'thing'},
                'pr_body_includes': {'some': 'thing'},
                'pr_body_excludes': {'some': 'thing'},
                'doesnt_matter': {'failure_level': 'error'},
            },
        }
        config = ConfigFactory.create(config_dict, include_pr=False)

        # Test settings
        assert config.settings == {'a': 1, 'b': 2}

        # Test checks
        check_configs = config.check_configs

        branch_name = check_configs['branch_name']
        assert branch_name.check_type == 'branch_name'
        assert branch_name.failure_level == 'warning'
        assert branch_name.options == {'pattern': '^TX-[0-9]+\-[\w\d\-]+$'}

        doesnt_matter = check_configs['doesnt_matter']
        assert doesnt_matter.check_type == 'doesnt_matter'
        assert doesnt_matter.failure_level == 'error'
        assert doesnt_matter.options == {}

        for check_name in PR_TYPES_CHECKS:
            assert check_name not in check_configs
