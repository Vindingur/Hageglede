# PURPOSE: Root-level db package that bridges pipeline.py imports to the real
#          src/hageglede/db/ module. Re-exports DatabaseManager and close_connection
#          from their respective submodules so that both "from db import X" and
#          "from db.submodule import X" resolve correctly.
# CONSUMED BY: scripts/pipeline.py (both import styles),
#              tests/test_bug_pipeline_db_import.py (import db)
# DEPENDS ON: db/db_ops.py, db/utils.py, src.hageglede.db.session, src.hageglede.db.schema
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

from db.db_ops import DatabaseManager
from db.utils import close_connection

__all__ = ["DatabaseManager", "close_connection", "init_db"]


def init_db(db_path: str = "hageglede.db") -> None:
    """Convenience initialiser — calls init_sqlite directly."""
    if not os.path.isabs(db_path):
        db_path = os.path.join(_project_root, db_path)
    init_sqlite(db_path)