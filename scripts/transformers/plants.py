"""Transform raw trait data from Artsdatabanken to Plant table schema."""
# PURPOSE: Pipeline transformer that normalizes Egenskapsbanken trait data into the
#          Plant table schema, dropping GBIF entirely. Generates meal_ideas from
#          edibility trait, yield_rating from effort_level heuristic, and
#          climate_zone_min/max from habitat.
# CONSUMED BY: scripts/pipeline.py (via transform_plants alias)
# DEPENDS ON: scripts/fetchers/artsdatabanken.py (ArtsdatabankenFetcher class for data shape)
# TEST: none

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def _extract_climate_zones(habitat: Optional[str]) -> tuple:
    """
    Derive climate_zone_min / climate_zone_max from habitat text.

    Artsdatabanken habitat strings often encode zone hints such as
    'til fjellet' (mountain), 'kyst', 'skogsmark' (forest).  We
    map these to numeric climate-range strings like '3', '7' etc.

    >>> _extract_climate_zones('kyst og skogsmark')
    ('3', '8')
    """
    if not habitat:
        return (None, None)
    text = habitat.lower()
    # Mountain / alpine species
    if "fjell" in text or "alpin" in text:
        return ("8", "11")
    # Coastal
    if "kyst" in text:
        return ("1", "4")
    # Forest / inland
    if "skog" in text:
        return ("3", "7")
    # Wetland
    if "myr" in text or "våt" in text:
        return ("2", "6")
    return ("1", "10")


def _effort_level_from_lifespan(life_form: Optional[str]) -> str:
    """
    Heuristic effort level based on life form.

    Returns 'low', 'medium' or 'high'.
    """
    if not life_form:
        return "medium"
    lf = life_form.lower()
    if lf in ("år", "ettårig", "annual"):
        return "low"
    if lf in ("staude", "flerårig", "perennial"):
        return "medium"
    if lf in ("tre", "busk", "shrub", "tree"):
        return "high"
    return "medium"


def _yield_rating_from_effort(effort: str) -> str:
    """
    Invert effort_level → yield_rating heuristic.

    Low-effort annual crops often give abundant yields in one season,
    whereas high-effort perennials/trees require more time but later
    pay off with larger cumulative yields.  We keep it simple.
    """
    mapping = {
        "low": "high",
        "medium": "medium",
        "high": "very-high",
    }
    return mapping.get((effort or "").lower(), "medium")


def _meal_ideas_from_edibility(edible_parts: Optional[str], species: Optional[str]) -> str:
    """
    Generate a plain-text list of meal ideas from edibility information.

    If Artsdatabanken provides no explicit edibility data we return an
    empty string so the downstream loader can store NULL.
    """
    if not edible_parts:
        return ""
    parts = [p.strip().lower() for p in str(edible_parts).split(",")]
    ideas: List[str] = []
    for part in parts:
        if "frukt" in part or "bær" in part or "berry" in part:
            ideas.append("fresh snack or jam")
        if "blad" in part or "leaf" in part:
            ideas.append("salad or sautée")
        if "rot" in part or "root" in part:
            ideas.append("roast or mash")
        if "frø" in part or "seed" in part:
            ideas.append("sprinkle on bread or cereal")
        if "blomst" in part or "flower" in part:
            ideas.append("garnish or tea")
    if not ideas:
        return ""
    return ", ".join(ideas)


def _sun_needs_from_habitat(habitat: Optional[str]) -> str:
    """
    Derive sun_needs from habitat description.
    """
    if not habitat:
        return "partial_sun"
    text = habitat.lower()
    if "åpen" in text or "lys" in text or "sol" in text:
        return "full_sun"
    if "skygg" in text or "mørk" in text or "skog" in text:
        return "partial_shade"
    return "partial_sun"


def _water_needs_from_habitat(habitat: Optional[str]) -> str:
    """
    Derive water_needs from habitat description.
    """
    if not habitat:
        return "moderate"
    text = habitat.lower()
    if "myr" in text or "våt" in text or "fuktig" in text or "fukter" in text:
        return "high"
    if "tørr" in text or "sand" in text or "steinete" in text or "fjell" in text:
        return "low"
    return "moderate"


def _soil_preference_from_habitat(habitat: Optional[str]) -> str:
    """
    Derive soil_preference from habitat description.
    """
    if not habitat:
        return "loam"
    text = habitat.lower()
    if "sand" in text or "klippe" in text:
        return "sandy"
    if "leire" in text or "fuktig" in text:
        return "clay"
    if "torv" in text or "myr" in text:
        return "peat"
    if "kalk" in text:
        return "chalky"
    return "loam"


def _parse_days_to_maturity(raw: Optional[Any]) -> Optional[int]:
    """
    Attempt to parse an integer from various raw formats.
    """
    if raw is None:
        return None
    try:
        return int(float(raw))
    except (ValueError, TypeError):
        return None


def transform_artsdatabanken_traits(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform Artsdatabanken Egenskapsbanken trait/occurrence data into
    a clean DataFrame aligned with the Plant table schema.

    Parameters
    ----------
    raw_data:
        List of dicts produced by ArtsdatabankenFetcher.fetch_plant_traits()
        or similar.  Expected keys include (but are not limited to):
        - scientificName / species
        - family
        - habitat
        - lifeForm
        - floweringPeriod
        - edibleParts (custom enrichment if available)
        - imageUrl (custom enrichment if available)

    Returns
    -------
    pd.DataFrame with columns:
        species, family, effort_level, climate_zone_min, climate_zone_max,
        yield_rating, meal_ideas, sun_needs, water_needs, soil_preference,
        days_to_maturity, image_url
    """
    if not raw_data:
        logger.warning("No Artsdatabanken trait data to transform")
        return pd.DataFrame(columns=[
            "species", "family", "effort_level", "climate_zone_min",
            "climate_zone_max", "yield_rating", "meal_ideas", "sun_needs",
            "water_needs", "soil_preference", "days_to_maturity", "image_url"
        ])

    records: List[Dict[str, Any]] = []
    for item in raw_data:
        # --- Species name --------------------------------------------------
        species = item.get("scientificName") or item.get("species") or ""
        # --- Family --------------------------------------------------------
        family = item.get("family") or ""
        # --- Habitat / life form -------------------------------------------
        habitat = item.get("habitat") or ""
        life_form = item.get("lifeForm") or ""

        # --- Derived fields ------------------------------------------------
        effort_level = _effort_level_from_lifespan(life_form)
        climate_zone_min, climate_zone_max = _extract_climate_zones(habitat)
        yield_rating = _yield_rating_from_effort(effort_level)
        meal_ideas = _meal_ideas_from_edibility(item.get("edibleParts"), species)
        sun_needs = _sun_needs_from_habitat(habitat)
        water_needs = _water_needs_from_habitat(habitat)
        soil_preference = _soil_preference_from_habitat(habitat)
        days_to_maturity = _parse_days_to_maturity(item.get("daysToMaturity"))
        image_url = item.get("imageUrl") or ""

        records.append({
            "species": species,
            "family": family,
            "effort_level": effort_level,
            "climate_zone_min": climate_zone_min,
            "climate_zone_max": climate_zone_max,
            "yield_rating": yield_rating,
            "meal_ideas": meal_ideas,
            "sun_needs": sun_needs,
            "water_needs": water_needs,
            "soil_preference": soil_preference,
            "days_to_maturity": days_to_maturity,
            "image_url": image_url,
            "source": "Artsdatabanken",
            "last_updated": datetime.now().isoformat(),
        })

    df = pd.DataFrame(records)
    logger.info(
        "Transformed %d Artsdatabanken trait records into aligned schema (%d columns)",
        len(df),
        len(df.columns),
    )
    return df


# ═══════════════════════════════════════════════════════════════════
# Compatibility alias — this is what the pipeline calls today.
# ═══════════════════════════════════════════════════════════════════
transform_plants = transform_artsdatabanken_traits


# Legacy GBIF aliases — removed.  Calling code should switch to the
# new transformer above.  Any existing imports will raise ImportError
# which is intentional (forces migration).
