from unittest.mock import patch

import pytest
from totem.checks.content import (
    BaseContentProvider,
    BaseGitContentProviderFactory,
    BaseGitServiceContentProviderFactory,
)


class TestBaseContentProvider:
    """Test the BaseContentProvider class."""

    def test_get_content_raises_not_implemented(self):
        provider = BaseContentProvider(repo_name='test', pr_num=99)
        with pytest.raises(NotImplementedError):
            provider.get_content()

    def test_create_pr_comment_raises_not_implemented(self):
        provider = BaseContentProvider(repo_name='test', pr_num=99)
        with pytest.raises(NotImplementedError):
            provider.create_pr_comment('...')

    def test_repo_name_property(self):
        provider = BaseContentProvider(repo_name='test', pr_num=99)
        assert provider.repo_name == 'test'

    def test_pr_number_property(self):
        provider = BaseContentProvider(repo_name='test', pr_num=99)
        assert provider.pr_number == 99


class Check1:
    pass


class Check2:
    pass


class Check3:
    pass


class TestBaseGitContentProviderFactory:
    """Test the BaseGitContentProviderFactory class."""

    def test_create_raises_not_implemented(self):
        factory = BaseGitContentProviderFactory()
        with pytest.raises(NotImplementedError):
            factory.create(None)

    def test_register(self):
        factory = BaseGitContentProviderFactory()
        factory.register('type1', Check1)
        factory.register('type2', Check2)

        assert factory._providers['type1'] == Check1
        assert factory._providers['type2'] == Check2
        assert factory._providers.get('type3') is None

    @patch('totem.checks.content.BaseGitContentProviderFactory._get_defaults')
    def test_default_registration_works(self, mock_get_defaults):
        mock_get_defaults.return_value = {'type1': Check1, 'type2': Check2}

        factory = BaseGitContentProviderFactory()
        assert factory._providers['type1'] == Check1
        assert factory._providers['type2'] == Check2
        assert factory._providers.get('type3') is None


class TestBaseGitServiceContentProviderFactory:
    """Test the BaseGitServiceContentProviderFactory class."""

    def test_constructor(self):
        factory = BaseGitServiceContentProviderFactory(repo_name='test', pr_num=99)
        assert factory.repo_name == 'test'
        assert factory.pr_num == 99

    def test_create_raises_not_implemented(self):
        factory = BaseGitServiceContentProviderFactory(repo_name='test', pr_num=99)
        with pytest.raises(NotImplementedError):
            factory.create(None)
