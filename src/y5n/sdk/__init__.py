"""Yakoon Python SDK — public API for commands.

Usage:
    from y5n.sdk import context, ports

    ctx = context.current()
    ports.provide("svc", {...})
    svc = ports.get("svc")

The SDK connects to the Host via YAK_ENDPOINT environment variable.
"""

from . import context
from . import ports

__all__ = ["context", "ports"]
