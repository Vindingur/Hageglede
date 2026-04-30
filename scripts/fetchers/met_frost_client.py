# PURPOSE: Low-level HTTP client for the Norwegian Meteorological Institute Frost API with retries and rate limiting
# CONSUMED BY: scripts.fetchers.met
# DEPENDS ON: requests
# TEST: none

"""
Low-level HTTP client for frost.met.no.

Handles:
- Authentication via X-Client-ID header
- Automatic retry with exponential backoff
- Rate-limit delay between requests
- Structured error types
"""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when MET Frost authentication fails."""


class RateLimitError(Exception):
    """Raised when MET Frost rate limit is exceeded."""


class MetFrostClient:
    """
    HTTP client for the MET Frost API (frost.met.no).

    Args:
        client_id: MET Frost API client ID.
        base_url: Frost API base URL (default ``https://frost.met.no``).
        timeout: Request timeout in seconds.
        max_retries: Max retry attempts on transient failures.
        rate_limit_delay: Minimum seconds to sleep between requests.
    """

    _last_request_time: float = 0.0

    def __init__(
        self,
        client_id: str,
        base_url: str = "https://frost.met.no",
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0,
    ):
        if not client_id:
            raise AuthenticationError("MET Frost client_id must be a non-empty string")
        self.client_id = client_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._max_retries = max_retries

        self.session = requests.Session()
        self.session.headers["X-Client-ID"] = client_id
        self.session.headers["Accept"] = "application/json"

        # Configure urllib3 retry for transient HTTP errors
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,
            status_forcelist={429, 500, 502, 503, 504},
            allowed_methods={"GET"},
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # ------------------------------------------------------------------
    # Observations API
    # ------------------------------------------------------------------
    def get_observations(
        self,
        sources: str,
        elements: Optional[str] = None,
        referencetime: Optional[str] = None,
        timeoffsets: str = "PT0H",
        timeresolutions: str = "PT1H",
        performancecategories: str = "C",
        exposurecategories: str = "1",
        levels: str = "0",
    ) -> Dict[str, Any]:
        """
        Fetch observations from ``/observations/v0.jsonld``.

        Args:
            sources: Comma-separated source IDs (e.g. ``"SN18700"``).
            elements: Comma-separated element IDs (e.g. ``"air_temperature,wind_speed"``).
            referencetime: ISO interval string (e.g. ``"2024-01-01/2024-01-07"``).
            timeoffsets: Time offset filter.
            timeresolutions: Time resolution filter.
            performancecategories: Quality category filter.
            exposurecategories: Exposure category filter.
            levels: Level filter.

        Returns:
            Parsed JSON dict from Frost API.

        Raises:
            AuthenticationError: On 401 / missing auth.
            RateLimitError: On 429 after exhausting retries.
            requests.HTTPError: On other non-2xx responses.
        """
        url = f"{self.base_url}/observations/v0.jsonld"
        params: Dict[str, Any] = {
            "sources": sources,
            "timeoffsets": timeoffsets,
            "timeresolutions": timeresolutions,
            "performancecategories": performancecategories,
            "exposurecategories": exposurecategories,
            "levels": levels,
            "fields": "sourceId,referenceTime,elementId,value,unit,timeOffset,timeResolution,level",
        }
        if elements:
            params["elements"] = elements
        if referencetime:
            params["referencetime"] = referencetime

        return self._request("GET", url, params=params)

    # ------------------------------------------------------------------
    # Sources API (for station discovery)
    # ------------------------------------------------------------------
    def get_sources(self, **filters: Any) -> Dict[str, Any]:
        """Fetch station/source metadata from ``/sources/v0.jsonld``."""
        url = f"{self.base_url}/sources/v0.jsonld"
        return self._request("GET", url, params=filters)

    def fetch_station_nearby(self, lat: float, lon: float) -> Optional[str]:
        """
        Retrieve the nearest MET station ID to a given lat/lon.

        Uses a simple bounding-box heuristic around the Frost sources
        endpoint. Returns ``None`` if no station is found.
        """
        try:
            data = self.get_sources(
                types="SensorSystem",
                country="NO",
                # Approximate 1° bounding box around the point
                geometry=f"nearest(POINT({lon} {lat}))",
                limit=1,
            )
            items = data.get("data", [])
            if items:
                return items[0].get("id")
        except Exception as exc:
            logger.warning("fetch_station_nearby failed: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Internal request machinery
    # ------------------------------------------------------------------
    def _request(self, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute a rate-limited HTTP request.  Returns parsed JSON.

        Applies an explicit inter-request sleep to respect the
        ``rate_limit_delay`` setting *in addition* to urllib3 retries.
        """
        self._enforce_rate_limit()

        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.exceptions.RequestException as exc:
            logger.error("Frost request failed: %s", exc)
            raise

        status = response.status_code
        if status == 401:
            raise AuthenticationError(
                f"MET Frost authentication failed (401). "
                f"Verify your MET_CLIENT_ID / MET_FROST_API_KEY. "
                f"Response: {response.text[:200]}"
            )
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            msg = (
                "MET Frost rate limit exceeded (429)."
            )
            if retry_after:
                msg += f" Retry-After: {retry_after}s."
            raise RateLimitError(msg)

        response.raise_for_status()
        return response.json()

    def _enforce_rate_limit(self) -> None:
        """Sleep until ``rate_limit_delay`` seconds have passed since the last request."""
        now = time.perf_counter()
        elapsed = now - MetFrostClient._last_request_time
        if elapsed >= self.rate_limit_delay:
            MetFrostClient._last_request_time = now
            return
        sleep_for = self.rate_limit_delay - elapsed
        logger.debug("Rate-limit sleep: %.3fs", sleep_for)
        time.sleep(sleep_for)
        MetFrostClient._last_request_time = time.perf_counter()
