"""
BridgeLab Toolkit
Alias Repository
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


# ============================================================
# Data Files
# ============================================================

DATA_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "data"
)

ALIASES_FILE = DATA_DIRECTORY / "aliases.yaml"


# ============================================================
# Alias Repository
# ============================================================

@dataclass(slots=True)
class AliasRepository:
    """
    Repository of aliases.

    Produces a lookup table mapping every alias to its
    canonical name.
    """

    aliases: dict[str, str] = field(
        init=False,
        default_factory=dict,
    )

    # ========================================================

    def __post_init__(self) -> None:

        self.aliases = self._load()

    # ========================================================

    def _load(
        self,
    ) -> dict[str, str]:
        """
        Load aliases from aliases.yaml.
        """

        if not ALIASES_FILE.exists():
            raise FileNotFoundError(
                f"Missing aliases file: {ALIASES_FILE}"
            )

        data = yaml.safe_load(
            ALIASES_FILE.read_text(
                encoding="utf-8",
            )
        )

        if not isinstance(data, dict):
            raise ValueError(
                "aliases.yaml must contain a mapping."
            )

        lookup: dict[str, str] = {}

        for canonical, aliases in data.items():

            canonical = str(canonical).strip().lower()

            if not canonical:
                continue

            # canonical name maps to itself
            lookup[canonical] = canonical

            if not aliases:
                continue

            for alias in aliases:

                alias = str(alias).strip().lower()

                if alias:
                    lookup[alias] = canonical

        return lookup

    # ========================================================

    def resolve(
        self,
        name: str,
    ) -> str:
        """
        Resolve a name to its canonical form.

        Returns the original name if no alias exists.
        """

        key = name.strip().lower()

        return self.aliases.get(key, key)
