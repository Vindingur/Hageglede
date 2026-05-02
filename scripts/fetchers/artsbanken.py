#!/usr/bin/env python3
# PURPOSE: Deprecation notice for old fetcher; all function bodies commented out.
# CONSUMED BY: none (deprecated)
# DEPENDS ON: none
# TEST: none

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEPRECATED — Do not use this file.  Use scripts/fetchers/artsdatabanken.py
# instead.  artsbanken.py is planned for deletion in the next cleanup pass.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
Artsbanken fetcher — DEPRECATED.

All functions below are disabled to prevent accidental pipeline execution.
The new fetcher (artsdatabanken.py) replaces every public interface here.
"""

import requests  # noqa: F401
import logging  # noqa: F401
import pandas as pd  # noqa: F401
from typing import List, Dict, Any, Optional  # noqa: F401
from datetime import datetime  # noqa: F401

logger = logging.getLogger(__name__)
BASE_URL = "https://api.artsdatabanken.no"


def __deprecated_call(function_name: str, *_args, **_kwargs):
    """Raise RuntimeError to prevent use of deprecated functions."""
    raise RuntimeError(
        f"artsbanken.{function_name} is DEPRECATED. "
        "Use scripts/fetchers/artsdatabanken.py instead."
    )


def fetch_artsdatabanken_data(output_path: str = "data/artsdatabanken_plants.csv") -> bool:  # noqa: ARG001
    """DEPRECATED — Use scripts/fetchers/artsdatabanken.py instead."""
    __deprecated_call("fetch_artsdatabanken_data")
    return False  # unreachable


def get_complete_plant_data() -> pd.DataFrame:  # type: ignore[empty-body]
    """DEPRECATED — Use scripts/fetchers/artsdatabanken.py instead."""
    __deprecated_call("get_complete_plant_data")
    return pd.DataFrame()  # unreachable


def get_plant_species_families() -> Dict[str, List[str]]:
    """DEPRECATED — Use scripts/fetchers/artsdatabanken.py instead."""
    __deprecated_call("get_plant_species_families")
    return {}  # unreachable


def fetch_all_plants(include_risk_assessment: bool = True) -> pd.DataFrame:  # noqa: ARG001  # type: ignore[empty-body]
    """DEPRECATED — Use scripts/fetchers/artsdatabanken.py instead."""
    __deprecated_call("fetch_all_plants")
    return pd.DataFrame()  # unreachable


if __name__ == "__main__":
    import sys

    print("artsbanken.py is DEPRECATED. Use artsdatabanken.py instead.", file=sys.stderr)
    sys.exit(1)
