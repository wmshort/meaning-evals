"""Key-value log lines on stderr, each carrying the invocation id of the command run.

HTTP-library loggers are held at WARNING: they would otherwise log every request line.
No log statement in the harness receives an API key.
"""

from __future__ import annotations

import logging
import sys
from typing import TextIO

FORMAT = (
    "ts=%(asctime)s level=%(levelname)s logger=%(name)s invocation=%(invocation_id)s %(message)s"
)
QUIET_LOGGERS = ("httpx", "httpx2", "httpcore", "httpcore2", "urllib3")


class _InvocationFilter(logging.Filter):
    def __init__(self, invocation_id: str) -> None:
        super().__init__()
        self.invocation_id = invocation_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.invocation_id = self.invocation_id
        return True


class _HarnessHandler(logging.StreamHandler[TextIO]):
    """Marks the handler this module installs, so a second call replaces it."""


def configure_logging(invocation_id: str, *, verbose: bool = False) -> None:
    root = logging.getLogger()
    for existing in [h for h in root.handlers if isinstance(h, _HarnessHandler)]:
        root.removeHandler(existing)
    handler = _HarnessHandler(sys.stderr)
    handler.addFilter(_InvocationFilter(invocation_id))
    handler.setFormatter(logging.Formatter(FORMAT))
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
