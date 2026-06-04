"""Short ID generation for batch tracking."""

import uuid


def generate_short_id(prefix: str = "") -> str:
    """Generate a short unique ID with optional prefix, e.g. 'bat_a1b2c3d4'."""
    short = uuid.uuid4().hex[:8]
    return f"{prefix}_{short}" if prefix else short
