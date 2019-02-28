import pytest
from totem.checks.config import CheckConfig
from totem.checks.core import Check, CheckFactory


class TestCheck:
    """Test the Check class."""

    def test_abstract_methods_raise_exception(self):
        check = Check(None)
        with pytest.raises(NotImplementedError):
            check.run({})

    def test_check_type_property_returns_proper_value(self):
        check = Check(CheckConfig('mytype', 'error'))
        assert check.check_type == 'mytype'

    def test_default_config_is_none(self):
        check = Check(CheckConfig('mytype', 'error'))
        assert check._default_config('anything') is None


class MyCheck1(Check):
    def run(self, content):
        return self._get_success()


class MyCheck2(Check):
    def run(self, content):
        return self._get_success()


class TestCheckFactory:
    """Test the CheckFactory class."""

    @pytest.fixture()
    def factory(self):
        """Return a new CheckFactory instance."""
        return CheckFactory()

    def test_registered_checks_success(self, factory):
        """Checks that have been registered in the factory cannot be created."""
        factory.register('check1', MyCheck1)
        factory.register('check2', MyCheck2)

        check = factory.create(CheckConfig('check1', 'error'))
        assert isinstance(check, MyCheck1)
        check = factory.create(CheckConfig('check2', 'error'))
        assert isinstance(check, MyCheck2)

    def test_unknown_checks_failure(self, factory):
        """A check that has not been registered in the factory cannot be created."""
        factory.register('check1', MyCheck1)
        factory.register('check2', MyCheck2)

        check = factory.create(CheckConfig('invalid', 'error'))
        assert check is None
