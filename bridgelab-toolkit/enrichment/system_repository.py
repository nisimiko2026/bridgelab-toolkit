"""
BridgeLab Toolkit
System Repository
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


# ============================================================
# Repository
# ============================================================

DATA_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "data"
)

SYSTEMS_FILE = DATA_DIRECTORY / "systems.yaml"


# ============================================================
# System Repository
# ============================================================

@dataclass(slots=True)
class SystemRepository:
    """
    Repository of known bidding systems.
    """

    systems: list[str] = field(
        init=False,
        default_factory=list,
    )

    # ========================================================

    def __post_init__(self) -> None:

        self.systems = self._load()

    # ========================================================

    def _load(
        self,
    ) -> list[str]:
        """
        Load systems from YAML.
        """

        if not SYSTEMS_FILE.exists():
            raise FileNotFoundError(
                f"Missing systems file: {SYSTEMS_FILE}"
            )

        data = yaml.safe_load(
            SYSTEMS_FILE.read_text(
                encoding="utf-8",
            )
        )

        if not isinstance(data, list):
            raise ValueError(
                "systems.yaml must contain a YAML list."
            )

        systems = []

        for item in data:

            name = str(item).strip().lower()

            if name:
                systems.append(name)

        return sorted(set(systems))
