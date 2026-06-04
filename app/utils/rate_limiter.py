"""IP-based rate limiting utilities using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address


def create_limiter() -> Limiter:
    """Create and configure the application rate limiter."""
    # TODO: Phase 1 — integrate with config for dynamic rate limits
    pass
