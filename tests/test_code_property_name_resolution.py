"""Offline tests for how the integration run resolves its property-key override.

The resolution order in conftest.code_property_name is the whole point of
that fixture, and every layer of it is a silent failure if it breaks: a run
that quietly falls back to the production key overwrites the property a live
Conditioned model is serving, and nothing about the test output would say so.

The .env layer in particular is load-bearing rather than decorative. The SDK
fixtures also read .env, but via pydantic-settings, which loads it into its
own settings model without exporting anything to os.environ — so reading the
file directly is the only way a value in .env reaches this fixture.
"""

from __future__ import annotations

from conditioning.codes import DEFAULT_CONDITIONING_KEY
from tests import conftest


class _FakeConfig:
    """Stands in for pytest's Config — only getoption() is used."""

    def __init__(self, value: str | None = None) -> None:
        self._value = value

    def getoption(self, _name: str) -> str | None:
        """Return the canned --code-property-name value."""
        return self._value


class _FakeRequest:
    """Stands in for pytest's FixtureRequest — only .config is used."""

    def __init__(self, config: _FakeConfig) -> None:
        self.config = config


def _resolve(request) -> str:
    """Call the fixture's underlying function, bypassing pytest injection."""
    return conftest.code_property_name.__wrapped__(request)


class TestEnvFileReader:
    """_from_env_file() reads the key out of .env, or returns None."""

    def test_reads_the_key_from_a_dotenv_file(self, tmp_path, monkeypatch):
        """Reads the key from a dotenv file."""
        env = tmp_path / ".env"
        env.write_text(
            'SPECKLE_TOKEN="irrelevant"\n'
            'CONDITIONING_CODE_PROPERTY_NAME="From Dotenv"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(conftest, "_ENV_FILE", env)
        assert conftest._from_env_file() == "From Dotenv"

    def test_absent_key_is_none_not_empty_string(self, tmp_path, monkeypatch):
        """Absent key is None, not an empty string."""
        env = tmp_path / ".env"
        env.write_text('SPECKLE_TOKEN="irrelevant"\n', encoding="utf-8")
        monkeypatch.setattr(conftest, "_ENV_FILE", env)
        assert conftest._from_env_file() is None

    def test_blank_value_is_none_so_it_falls_through(self, tmp_path, monkeypatch):
        """Blank value is None so it falls through.

        An empty assignment must not win the `or` chain and hand an empty
        property key to every wall object.
        """
        env = tmp_path / ".env"
        env.write_text('CONDITIONING_CODE_PROPERTY_NAME=""\n', encoding="utf-8")
        monkeypatch.setattr(conftest, "_ENV_FILE", env)
        assert conftest._from_env_file() is None

    def test_missing_dotenv_file_is_not_an_error(self, tmp_path, monkeypatch):
        """Missing dotenv file is not an error."""
        monkeypatch.setattr(conftest, "_ENV_FILE", tmp_path / "nope.env")
        assert conftest._from_env_file() is None


class TestResolutionOrder:
    """Flag beats real env, real env beats .env, .env beats the default."""

    def test_default_when_nothing_is_configured(self, monkeypatch):
        """Default when nothing is configured."""
        monkeypatch.delenv(conftest._ENV_VAR, raising=False)
        monkeypatch.setattr(conftest, "_from_env_file", lambda: None)
        assert _resolve(_FakeRequest(_FakeConfig(None))) == DEFAULT_CONDITIONING_KEY

    def test_dotenv_beats_the_default(self, monkeypatch):
        """Dotenv beats the default."""
        monkeypatch.delenv(conftest._ENV_VAR, raising=False)
        monkeypatch.setattr(conftest, "_from_env_file", lambda: "From Dotenv")
        assert _resolve(_FakeRequest(_FakeConfig(None))) == "From Dotenv"

    def test_real_environment_beats_dotenv(self, monkeypatch):
        """Real environment beats dotenv."""
        monkeypatch.setenv(conftest._ENV_VAR, "From Environ")
        monkeypatch.setattr(conftest, "_from_env_file", lambda: "From Dotenv")
        assert _resolve(_FakeRequest(_FakeConfig(None))) == "From Environ"

    def test_flag_beats_everything(self, monkeypatch):
        """Flag beats everything."""
        monkeypatch.setenv(conftest._ENV_VAR, "From Environ")
        monkeypatch.setattr(conftest, "_from_env_file", lambda: "From Dotenv")
        assert _resolve(_FakeRequest(_FakeConfig("From Flag"))) == "From Flag"
