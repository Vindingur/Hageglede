# PURPOSE: Provides the DatabaseManager class at the db.db_ops submodule path
#          that pipeline.py's init_db() function imports.
# CONSUMED BY: scripts/pipeline.py (init_db via from db.db_ops import DatabaseManager),
#              tests/test_bug_pipeline_db_import.py (from db.db_ops import DatabaseManager)
# DEPENDS ON: src.hageglede.db.session (init_sqlite), db/__init__.py (sys.path setup)
# TEST: tests/test_bug_pipeline_db_import.py

"""Database operations — DatabaseManager wrapper around init_sqlite."""

import os
import sys

# Use the same sys.path setup that db/__init__.py performs so that
# src/hageglede.db.* imports resolve correctly from the project root.
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