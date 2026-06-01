# PURPOSE: Root-level db package that bridges pipeline.py imports to the real
#          src/hageglede/db/ module. Provides DatabaseManager (wrapping
#          init_sqlite) and close_connection so that pipeline.py's existing
#          import statements resolve without changing the pipeline.
# CONSUMED BY: scripts/pipeline.py
# DEPENDS ON: src.hageglede.db.session (init_sqlite, get_session), src.hageglede.db.schema (Base)
# TEST: tests/test_bug_pipeline_db_import.py

"""Root-level db package — bridges pipeline imports to src/hageglede/db."""

import os
import sys

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that ``src.hageglede.db``
# can be imported from the project root even when ``PYTHONPATH`` is unset.
# This is the production scenario: ``python3 -m scripts.pipeline`` from
# ``/root/Hageglede`` with no special environment variables.
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_project_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from hageglede.db.session import init_sqlite, get_session
from hageglede.db.schema import Base

__all__ = ["DatabaseManager", "close_connection", "init_db"]


class DatabaseManager:
    """Thin adapter that matches the interface pipeline.py expects."""

    def __init__(self, db_path: str = "hageglede.db"):
        # Normalise a project-root-relative path like "hageglede.db"
        # into an absolute path so init_sqlite always opens the expected file
        # regardless of the caller's CWD.
        if not os.path.isabs(db_path):
            db_path = os.path.join(_project_root, db_path)
        self.db_path = db_path

    def init_db(self) -> None:
        """Create all tables via the real init_sqlite."""
        init_sqlite(self.db_path)


def close_connection() -> None:
    """No-op close — sessions are managed per-context via get_session.

    This function exists solely to satisfy the ``finally`` block in
    pipeline's ``run_pipeline()`` which calls ``close_connection()``.
    There is no global connection handle to close because every caller
    that needs a session opens one via the context manager.
    """
    pass


def init_db(db_path: str = "hageglede.db") -> None:
    """Convenience initialiser — calls init_sqlite directly."""
    if not os.path.isabs(db_path):
        db_path = os.path.join(_project_root, db_path)
    init_sqlite(db_path)