# PURPOSE: Defines close_connection (no-op) and init_db convenience function
#          used by pipeline.py's run_pipeline() finally block and init helpers.
# CONSUMED BY: scripts/pipeline.py (via `from db.utils import close_connection`),
#              tests/test_bug_pipeline_db_import.py
# DEPENDS ON: db/__init__.py (must run first for sys.path setup),
#             src.hageglede.db.session (init_sqlite)
# TEST: tests/test_bug_pipeline_db_import.py

"""Utility functions — close_connection and init_db for the pipeline."""

import os

# ---------------------------------------------------------------------------
# _project_root is the directory containing db/ (i.e. the project root).
# Used by init_db to normalise relative paths.
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from hageglede.db.session import init_sqlite  # noqa: E402

__all__ = ["close_connection", "init_db"]


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