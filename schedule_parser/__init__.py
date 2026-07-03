"""Deterministic Excel schedule parser package."""

from .schema import ParsedSchedule

__all__ = ["ParsedSchedule", "parse_oil_street_schedule", "parse_d_and_g_schedule"]


def parse_oil_street_schedule(*args, **kwargs):
    from .oil_street import parse_oil_street_schedule as _parse_oil_street_schedule

    return _parse_oil_street_schedule(*args, **kwargs)


def parse_d_and_g_schedule(*args, **kwargs):
    from .d_and_g import parse_d_and_g_schedule as _parse_d_and_g_schedule

    return _parse_d_and_g_schedule(*args, **kwargs)
