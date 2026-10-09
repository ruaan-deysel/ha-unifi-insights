# Copyright (c) 2026 Ruaan Deysel
"""Validation error helpers for API response handling."""

from pydantic import ValidationError


def sanitized_validation_fields(err: ValidationError) -> str:
    """Return sorted, de-duplicated validation field names without values."""
    field_names = [str((item.get("loc") or ("root",))[-1]) for item in err.errors()]
    return ", ".join(sorted(set(field_names)))
