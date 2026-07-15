"""Command context — access request, session, path.

Usage:
    from y5n.sdk import context
    ctx = context.current()
    print(ctx.path)
    print(ctx["request"])
"""

import sys

from y5n.base.runtime.context import context as _base_context

sys.modules[__name__] = _base_context
