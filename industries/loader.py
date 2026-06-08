"""Load and validate industry YAML configs."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

from industries._schema import Industry

logger = logging.getLogger(__name__)

DEFAULT_DIRECTORY = Path(__file__).parent


class IndustryNotFoundError(FileNotFoundError):
    pass


def load_industry(
    slug: str,
    directory: Optional[Path] = None,
) -> Industry:
    """Load and validate a single industry YAML by slug."""
    d = directory or DEFAULT_DIRECTORY
    path = d / f"{slug}.yaml"
    if not path.exists():
        raise IndustryNotFoundError(f"No industry YAML at {path}")
    with path.open("r") as f:
        raw = yaml.safe_load(f) or {}
    try:
        return Industry(**raw)
    except Exception as exc:
        logger.error("[Industries] Failed to parse %s: %s", path, exc)
        raise


def load_all_industries(
    directory: Optional[Path] = None,
) -> dict[str, Industry]:
    """Load every .yaml file in directory, returning {slug: Industry}."""
    d = directory or DEFAULT_DIRECTORY
    result: dict[str, Industry] = {}
    for path in sorted(d.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        try:
            with path.open("r") as f:
                raw = yaml.safe_load(f) or {}
            ind = Industry(**raw)
            result[ind.slug] = ind
        except Exception as exc:
            logger.warning("[Industries] Skipping %s: %s", path.name, exc)
            continue
    return result
