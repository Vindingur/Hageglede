# PURPOSE: New module containing the DatabaseManager class extracted from
#          db/__init__.py. Resolves `from db.db_ops import DatabaseManager`
#          in scripts/pipeline.py's init_db().
# CONSUMED BY: scripts/pipeline.py (init_db function), db/__init__.py (re-exports DatabaseManager)
# DEPENDS ON: hageglede.db.session (init_sqlite)
# TEST: tests/test_bug_pipeline_db_import.py

"""Database operations adapter for the root-level db bridge package."""

import os
import sys

# Ensure src/ is importable — this module may be imported before db/__init__.py
# has run its sys.path setup (e.g. via `from db.db_ops import DatabaseManager`
# in pipeline.py). The root-level db/__init__.py normally handles this, but
# CPython processes imports as: find db/ → run db/__init__.py → then look for
# db/db_ops.py. So by the time we execute, sys.path is already set up.
# Keep the defensive guard for any edge case.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src = os.path.join(_project_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from hageglede.db.session import init_sqlite


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
