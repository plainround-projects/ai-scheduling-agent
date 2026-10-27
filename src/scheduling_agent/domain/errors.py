"""Named errors. Callers catch these, never a vendor SDK's exception types."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every error this package raises on purpose."""


class ModelError(DomainError):
    """A model call failed."""


class TransientModelError(ModelError):
    """The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."""


class PermanentModelError(ModelError):
    """Repeating the call cannot help: a bad request, a bad key, a refusal to parse."""


class RecordingMissing(PermanentModelError):
    """The recorded adapter has no response for this request. Re-record with `make record`."""


class UnsupportedParameter(PermanentModelError):
    """The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."""


class BudgetExceeded(DomainError):
    """A run hit one of its caps: steps, tokens or wall-clock time."""

    def __init__(self, cap: str, message: str) -> None:
        super().__init__(message)
        self.cap = cap


class CalendarError(DomainError):
    """The calendar refused or could not do what was asked."""


class UnknownPerson(CalendarError):
    """A name that is not one of the calendar's people."""


class UnknownEvent(CalendarError):
    """No event with that id."""


class SlotUnavailable(CalendarError):
    """A person is already busy at that time."""


class InvalidSlot(CalendarError):
    """The time is outside working hours, off the half-hour grid, on a weekend or has a bad length."""


class ApprovalError(DomainError):
    """An approval is missing, not approved, or was granted for a different proposal."""


class AlreadyCancelled(CalendarError):
    """The event is already cancelled."""


class IdempotencyConflict(CalendarError):
    """An Idempotency-Key was reused for a different request."""


class CalendarUnavailable(CalendarError):
    """The calendar service did not answer (timeout, connection refused, 5xx)."""
