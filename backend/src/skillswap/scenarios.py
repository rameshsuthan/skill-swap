"""Explicit fictional-data maintenance scenarios, never exposed as model tools."""

from .models import LocalAvailabilityInput
from .scheduling import normalize_window


def memory_alternatives(repository):
    windows = [
        LocalAvailabilityInput(
            start_local="2026-10-26T14:00", end_local="2026-10-26T14:30", timezone="America/Toronto"
        ),
        LocalAvailabilityInput(
            start_local="2026-10-27T10:00", end_local="2026-10-27T10:30", timezone="America/Toronto"
        ),
    ]
    repository.update_profile(
        "olivia", availability=[normalize_window(w).model_dump() for w in windows]
    )
