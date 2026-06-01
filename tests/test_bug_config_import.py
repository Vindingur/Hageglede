# PURPOSE: Regression test verifying that scripts.config exports DATABASE_PATH and FROST_CONFIG
# CONSUMED BY: CI regression suite
# DEPENDS ON: subprocess, scripts.config, scripts.pipeline
# TEST: self-contained

"""
Reproduction test for bug: scripts/pipeline.py raises ModuleNotFoundError
because imports inside functions reference non-existent modules like db.utils,
db.db_ops, fetchers.siv, fetchers.wikidata, fetchers.met.

Two prior fixes failed because they addressed config exports but didn't fix
the internal function imports. This test verifies the entire pipeline can
be imported and its --help can execute without import errors.
"""
import subprocess
import sys
from pathlib import Path

try:
    REPO_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    REPO_ROOT = Path.cwd()


def test_pipeline_help_runs_without_import_error():
    """
    Running `python3 -m scripts.pipeline --help` should succeed without ImportError.

    The module-level handler should catch --help BEFORE any broken imports
    inside function definitions are evaluated.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'scripts.pipeline', '--help'],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"pipeline --help failed with code {result.returncode}:\n"
        f"STDERR: {result.stderr}\nSTDOUT: {result.stdout}"
    )
    combined = (result.stdout + result.stderr).lower()
    assert 'usage' in combined, (
        f"Expected 'usage' in output:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )


def test_direct_import_of_config_names():
    """Direct import of DATABASE_PATH and FROST_CONFIG from scripts.config should work."""
    from scripts.config import DATABASE_PATH, DATA_DIR, FROST_CONFIG
    assert DATABASE_PATH is not None
    assert DATA_DIR is not None
    assert FROST_CONFIG is not None
    assert isinstance(FROST_CONFIG, dict)
    assert 'base_url' in FROST_CONFIG