"""Shared API dependencies — rate limiter and common utilities."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# IP-based rate limiter (no auth, so we rate-limit by client IP)
limiter = Limiter(key_func=get_remote_address)
