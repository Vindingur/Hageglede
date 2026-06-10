# PURPOSE: Provides the close_connection function at the db.utils submodule path
#          that pipeline.py's run_pipeline() finally block imports.
# CONSUMED BY: scripts/pipeline.py (run_pipeline finally via from db.utils import close_connection),
#              tests/test_bug_pipeline_db_import.py (from db.utils import close_connection)
# DEPENDS ON: none
# TEST: tests/test_bug_pipeline_db_import.py

"""db.utils — Helper functions extracted from db/__init__.py"""

__all__ = ["close_connection"]


def close_connection() -> None:
    """No-op close — sessions are managed per-context via get_session.

    This function exists solely to satisfy the ``finally`` block in
    pipeline's ``run_pipeline()`` which calls ``close_connection()``.
    There is no global connection handle to close because every caller
    that needs a session opens one via the context manager.
    """
    pass
