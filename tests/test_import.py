"""Smoke test - verify the package is importable."""

from mcp_bouncer import __version__


def test_version_exists():
    assert __version__


def test_version_is_string():
    assert isinstance(__version__, str)
