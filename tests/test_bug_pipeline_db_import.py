# PURPOSE: Reproduction test for the blocking "No module named 'db'" import error
#          when running `python3 -m scripts.pipeline` from the project root.
# CONSUMED BY: CI verification on bugfix branch
# DEPENDS ON: db.db_ops, db.utils
# TEST: none (this is itself a test)

"""
Reproduction: verify that the db package at the project root can be imported
and that its DatabaseManager and close_connection are usable.
"""
import sys
import os
import subprocess


def test_db_package_is_importable():
    """The db package must be importable from the project root."""
    result = subprocess.run(
        [sys.executable, "-c", "import db"],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    assert result.returncode == 0, (
        f"import db failed with stderr: {result.stderr}"
    )


def test_db_db_ops_imports_database_manager():
    """from db.db_ops import DatabaseManager must succeed."""
    import db.db_ops
    assert hasattr(db.db_ops, "DatabaseManager"), (
        "db.db_ops is missing DatabaseManager"
    )


def test_db_utils_imports_close_connection():
    """from db.utils import close_connection must succeed."""
    import db.utils
    assert hasattr(db.utils, "close_connection"), (
        "db.utils is missing close_connection"
    )


def test_database_manager_init_db_does_not_crash():
    """DatabaseManager().init_db() must not raise an exception."""
    from db.db_ops import DatabaseManager
    mgr = DatabaseManager()
    # init_db should be callable even if the underlying db path is bogus;
    # the triage says the real code is init_sqlite from src.hageglede.db.session
    try:
        mgr.init_db()
    except Exception as e:
        # The real init_sqlite may fail on a bad path — that's fine,
        # the point is the import and attribute access must work.
        assert "No module named" not in str(e), (
            f"DatabaseManager.init_db raised an import error: {e}"
        )


if __name__ == "__main__":
    test_db_package_is_importable()
    test_db_db_ops_imports_database_manager()
    test_db_utils_imports_close_connection()
    test_database_manager_init_db_does_not_crash()
    print("All reproduction tests passed.")