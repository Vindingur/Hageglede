# PURPOSE: Root-level db package that bridges pipeline.py imports to the real
#          src/hageglede/db/ module. Re-exports DatabaseManager from db_ops
#          and close_connection/init_db from utils so that 'from db import ...'
#          and submodule imports both resolve.
# CONSUMED BY: scripts/pipeline.py, db/db_ops.py, db/utils.py
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
# This must run BEFORE the submodule imports below because db_ops.py and
# utils.py need src/hageglede on sys.path for their own imports.
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_project_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from .db_ops import DatabaseManager          # noqa: E402
from .utils import close_connection, init_db # noqa: E402

__all__ = ["DatabaseManager", "close_connection", "init_db"]