"""The e2e tests reuse the fixture that starts the calendar service as a real process."""

from tests.integration.conftest import service

__all__ = ["service"]
