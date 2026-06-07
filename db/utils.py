# PURPOSE: New module containing close_connection() and init_db() extracted
#          from db/__init__.py. Resolves `from db.utils import close_connection`
#          in scripts/pipeline.py's run_pipeline() finally block.
# CONSUMED BY: scripts/pipeline.py (run_pipeline finally block), db/__init__.py (re-exports close_connection and init_db)
# DEPENDS ON: hageglede.db.session (init_sqlite)
# TEST: tests/test_bug_pipeline_db_import.py

"""Utility functions for the root-level db bridge package."""

import os
import sys

# Same defensive sys.path guard as db_ops.py — see comment there.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src = os.path.join(_project_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from hageglede.db.session import init_sqlite


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
