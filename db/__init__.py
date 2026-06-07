# PURPOSE: Root-level db package that bridges pipeline.py imports to the real
#          src/hageglede/db/ module. Re-exports DatabaseManager, close_connection,
#          and init_db from the new submodules db.db_ops and db.utils so that
#          pipeline.py's `from db.db_ops import ...` and `from db.utils import ...`
#          resolve correctly.
# CONSUMED BY: scripts/pipeline.py (via submodule imports)
# DEPENDS ON: db.db_ops (DatabaseManager), db.utils (close_connection, init_db), hageglede.db.session, hageglede.db.schema
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

# Re-export from the submodules so the package API remains stable.
from .db_ops import DatabaseManager          # noqa: F401
from .utils import close_connection, init_db  # noqa: F401

__all__ = ["DatabaseManager", "close_connection", "init_db"]
