# PURPOSE: Live API fetcher for Egenskapsbanken providing plant trait data
#          (effort level, habitat, edibility) to the Hageglede data pipeline.
# CONSUMED BY: scripts/fetchers/__init__.py re-exports, scripts/pipeline.py may import ArtsdatabankenClient in future, plant_loader may consume trait data
# DEPENDS ON: requests external library
# TEST: none
"""
Fetcher for plant trait data from Artsdatabanken's Egenskapsbanken API.

Egenskapsbanken (Artsdatabanken's trait bank) provides ecological and
cultural trait data for Norwegian species—including effort levels,
habitat preferences, and edibility for garden-relevant plants.
API Documentation: https://egenskapsbanken.artsdatabanken.no/api/v1/
"""
import logging
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


# Egenskapsbanken trait identifiers used by the API
TRAIT_EFFORT_LEVEL = "tidsyn-vedlikeholdsinnsats"   # maintenance effort
TRAIT_HABITAT = "hovedhabitat"                      # primary habitat
TRAIT_EDIBILITY = "spiselighet"                     # edibility


class ArtsdatabankenFetcher:
    """Fetch plant trait data from Egenskapsbanken (Artsdatabanken) API."""

    BASE_URL = "https://egenskapsbanken.artsdatabanken.no/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Artsdatabanken fetcher.

        Args:
            api_key: Optional API key for authenticated requests.
                     Public endpoints may work without key.
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

        # Common headers
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Hageglede/1.0 Data Pipeline"
        })

    # ------------------------------------------------------------------
    #  Species endpoints
    # ------------------------------------------------------------------

    def search_species(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for species by scientific or Norwegian name.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of species records.
        """
        endpoint = f"{self.BASE_URL}/species"
        params = {"search": query, "limit": limit}

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", data.get("data", []))
            logger.info("Found %d species matching '%s'", len(items), query)
            return items
        except requests.exceptions.RequestException as exc:
            logger.error("Error searching species for '%s': %s", query, exc)
            return []

    def get_species_by_id(self, taxon_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific species.

        Args:
            taxon_id: Artsdatabanken taxon identifier.

        Returns:
            Species details dict or None if error.
        """
        endpoint = f"{self.BASE_URL}/species/{taxon_id}"
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error("Error fetching species %s: %s", taxon_id, exc)
            return None

    # ------------------------------------------------------------------
    #  Trait / egenskap endpoints
    # ------------------------------------------------------------------

    def get_traits_for_species(self, taxon_id: str) -> List[Dict]:
        """
        Fetch all registered traits for a given species.

        Args:
            taxon_id: Artsdatabanken taxon identifier.

        Returns:
            List of trait records (each containing trait name, value,
            confidence, source, etc.).
        """
        endpoint = f"{self.BASE_URL}/species/{taxon_id}/traits"
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", data.get("data", []))
            logger.info("Fetched %d traits for species %s", len(items), taxon_id)
            return items
        except requests.exceptions.RequestException as exc:
            logger.error("Error fetching traits for %s: %s", taxon_id, exc)
            return []

    def _get_trait_value(self, taxon_id: str, trait_key: str) -> Optional[str]:
        """
        Internal helper: query live trait endpoint and extract the value.

        Some Egenskapsbanken endpoints return the evaluated trait directly
        under ``/species/{id}/traits/{trait_key}``; this method attempts
        that shortcut first and falls back to scanning the full trait list
        if the endpoint is not available.
        """
        # 1) try the direct trait endpoint
        direct_url = f"{self.BASE_URL}/species/{taxon_id}/traits/{trait_key}"
        try:
            resp = self.session.get(direct_url)
            if resp.status_code == 200:
                payload = resp.json()
                # common shapes: {"value": "..."} or {"valueName": "..."}
                if isinstance(payload, dict):
                    for key in ("value", "valueName", "verdi", "navn"):
                        candidate = payload.get(key)
                        if candidate is not None:
                            return str(candidate).strip()
        except requests.exceptions.RequestException:
            pass  # fall through to generic list scan

        # 2) fallback: scan all traits
        traits = self.get_traits_for_species(taxon_id)
        for trait in traits:
            t_key = trait.get("key") or trait.get("id") or trait.get("traitId", "")
            t_name = trait.get("name") or trait.get("traitName") or trait.get("egenskap", "")
            if t_key == trait_key or trait_key.lower() in t_name.lower():
                for vkey in ("value", "valueName", "verdi", "navn"):
                    candidate = trait.get(vkey)
                    if candidate is not None:
                        return str(candidate).strip()
        return None

    def get_effort_level(self, taxon_id: str) -> Optional[str]:
        """
        Fetch the maintenance-effort level (tidsyn-vedlikeholdsinnsats)
        for a species.

        Args:
            taxon_id: Artsdatabanken taxon identifier.

        Returns:
            Effort-level string (e.g. 'Lav', 'Middels', 'Høy') or None.
        """
        return self._get_trait_value(taxon_id, TRAIT_EFFORT_LEVEL)

    def get_habitat(self, taxon_id: str) -> Optional[str]:
        """
        Fetch the primary habitat (hovedhabitat) for a species.

        Args:
            taxon_id: Artsdatabanken taxon identifier.

        Returns:
            Habitat string (e.g. 'Skog', 'Eng', 'Hage') or None.
        """
        return self._get_trait_value(taxon_id, TRAIT_HABITAT)

    def get_edibility(self, taxon_id: str) -> Optional[str]:
        """
        Fetch the edibility (spiselighet) for a species.

        Args:
            taxon_id: Artsdatabanken taxon identifier.

        Returns:
            Edibility string (e.g. 'Spiselig', 'Giftig') or None.
        """
        return self._get_trait_value(taxon_id, TRAIT_EDIBILITY)

    # ------------------------------------------------------------------
    #  Convenience / batch helpers
    # ------------------------------------------------------------------

    def enrich_plant_dict(self, plant: Dict) -> Dict:
        """
        Enrich a plant dict with trait data fetched from Egenskapsbanken.

        The input dict must contain either ``taxon_id`` or ``id`` key.
        The returned dict will have new keys ``effort_level``, ``habitat``,
        and ``edibility`` (set to None when data is unavailable).

        Args:
            plant: Dictionary representing a plant (must contain taxon id).

        Returns:
            New dict with added trait fields.
        """
        taxon_id = plant.get("taxon_id") or plant.get("id")
        if not taxon_id:
            logger.warning("Plant dict has no taxon_id or id; skipping enrichment.")
            return {**plant, "effort_level": None, "habitat": None, "edibility": None}

        # Expose all three traits in parallel (lightweight IO)
        effort = self.get_effort_level(taxon_id)
        habitat = self.get_habitat(taxon_id)
        edibility = self.get_edibility(taxon_id)

        return {
            **plant,
            "effort_level": effort,
            "habitat": habitat,
            "edibility": edibility,
        }

    def fetch_plants_with_traits(
        self,
        plant_records: List[Dict],
        delay: float = 0.3,
    ) -> List[Dict]:
        """
        Batch-enrich a list of plant records with Egenskapsbanken traits.

        Args:
            plant_records: List of plant dicts (needs ``taxon_id`` or ``id``).
            delay: Seconds to sleep between requests (rate-limit politeness).

        Returns:
            List of enriched plant dicts.
        """
        enriched = []
        for idx, plant in enumerate(plant_records, start=1):
            logger.info("Enriching plant %d/%d …", idx, len(plant_records))
            enriched.append(self.enrich_plant_dict(plant))
            if delay and idx != len(plant_records):
                time.sleep(delay)
        return enriched


# ----------------------------------------------------------------------
#  Backwards-compatible alias expected by consumers
# ----------------------------------------------------------------------
ArtsdatabankenClient = ArtsdatabankenFetcher
