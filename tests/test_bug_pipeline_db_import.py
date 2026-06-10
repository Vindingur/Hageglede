# PURPOSE: Reproduction test that verifies db.db_ops.DatabaseManager and
#          db.utils.close_connection are importable via their submodule paths.
# CONSUMED BY: CI verification (fix_bug workflow)
# DEPENDS ON: db/db_ops.py, db/utils.py, db/__init__.py
# TEST: none (self — this is the reproduction)

"""Verify that db.db_ops and db.utils exist and export the expected symbols."""

import importlib
import inspect
import sys


def test_can_import_database_manager_from_db_ops():
    """`from db.db_ops import DatabaseManager` must succeed."""
    db_ops = importlib.import_module("db.db_ops")
    assert hasattr(db_ops, "DatabaseManager"), (
        "db.db_ops does not export DatabaseManager"
    )
    assert inspect.isclass(db_ops.DatabaseManager), (
        "db.db_ops.DatabaseManager should be a class"
    )


def test_can_import_close_connection_from_db_utils():
    """`from db.utils import close_connection` must succeed."""
    db_utils = importlib.import_module("db.utils")
    assert hasattr(db_utils, "close_connection"), (
        "db.utils does not export close_connection"
    )
    assert callable(db_utils.close_connection), (
        "db.utils.close_connection should be callable"
    )


def test_backward_compat_from_db_package():
    """`from db import DatabaseManager, close_connection` must still work."""
    import db
    assert hasattr(db, "DatabaseManager"), "db.DatabaseManager missing"
    assert hasattr(db, "close_connection"), "db.close_connection missing"
    assert inspect.isclass(db.DatabaseManager)
    assert callable(db.close_connection)


def test_database_manager_init_db_works(tmp_path):
    """DatabaseManager().init_db() should create a SQLite database file."""
    from db.db_ops import DatabaseManager

    db_file = tmp_path / "test_hageglede.db"
    mgr = DatabaseManager(db_path=str(db_file))
    mgr.init_db()

    assert db_file.exists(), f"Database file {db_file} was not created"
    assert db_file.stat().st_size > 0, "Database file is empty"


def test_close_connection_is_noop():
    """close_connection() is a no-op that does not raise."""
    from db.utils import close_connection

    # Should not raise under any circumstances
    close_connection()
    close_connection()
    close_connection()


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
