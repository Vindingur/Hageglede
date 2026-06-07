# PURPOSE: Defines DatabaseManager class — a thin adapter that wraps
#          src.hageglede.db.session.init_sqlite for pipeline.py.
# CONSUMED BY: scripts/pipeline.py (via `from db.db_ops import DatabaseManager`),
#              tests/test_bug_pipeline_db_import.py
# DEPENDS ON: db/__init__.py (must run first for sys.path setup),
#             src.hageglede.db.session (init_sqlite, get_session),
#             src.hageglede.db.schema (Base)
# TEST: tests/test_bug_pipeline_db_import.py

"""Database operations — DatabaseManager adapter for the pipeline."""

import os

# ---------------------------------------------------------------------------
# _project_root is the directory containing db/ (i.e. the project root).
# It is used to normalise relative db_path arguments into absolute paths
# so that init_sqlite always opens the expected file regardless of CWD.
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from hageglede.db.session import init_sqlite, get_session  # noqa: E402
from hageglede.db.schema import Base                       # noqa: E402

__all__ = ["DatabaseManager"]


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