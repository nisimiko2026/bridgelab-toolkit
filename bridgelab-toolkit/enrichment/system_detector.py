"""
BridgeLab Toolkit
System Detector
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from enrichment.system_repository import SystemRepository


# ============================================================
# System Detector
# ============================================================

@dataclass(slots=True)
class SystemDetector:
    """
    Detect bidding systems mentioned in text.
    """

    repository: SystemRepository = field(
        default_factory=SystemRepository
    )

    # ========================================================

    def detect(
        self,
        text: str,
    ) -> list[str]:
        """
        Detect bidding systems in text.
        """

        found: set[str] = set()

        content = text.lower()

        for system in self.repository.systems:

            pattern = (
                r"\b"
                + re.escape(system.lower())
                + r"\b"
            )

            if re.search(pattern, content):
                found.add(system)

        return sorted(found)

    # ========================================================

    def contains(
        self,
        text: str,
        system: str,
    ) -> bool:
        """
        Determine whether a system is present.
        """

        pattern = (
            r"\b"
            + re.escape(system.lower())
            + r"\b"
        )

        return re.search(
            pattern,
            text.lower(),
        ) is not None
