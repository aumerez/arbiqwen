"""Shared rate limiter (slowapi).

A single process-wide limiter keyed on client IP. Routes opt in with the
`@limiter.limit(...)` decorator (they must take a `request: Request` param).
In-memory storage is fine because the app runs single-worker.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
