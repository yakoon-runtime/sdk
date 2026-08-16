"""Security contracts between commands and the runtime.

This module re-exports the shared security vocabulary for packs. Commands
should program against the SDK, never against `runtime.api` directly —
the SDK is the stable public API.

The enum itself lives in the runtime API; this module is the pack-facing
view of the contract. A command expresses its *desired* session mode when
authenticating (e.g. ``su --administrative`` → ``SecurityContext.ADMINISTRATIVE``);
the runtime realizes it as the session's security context.
"""

from __future__ import annotations

from y5n.runtime.api.runtime.sessions import SecurityContext

__all__ = [
    "SecurityContext",
]
