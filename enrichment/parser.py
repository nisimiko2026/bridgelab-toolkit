"""
BridgeLab Toolkit
Metadata Parser
"""

from __future__ import annotations

from core.models import Metadata


# ============================================================
# Metadata Parser
# ============================================================

class MetadataParser:
    """
    Parse and serialize BridgeLab YAML metadata.
    """

    # ========================================================
    # Parse
    # ========================================================

    def parse(
        self,
        text: str,
    ) -> Metadata:
        """
        Parse YAML front matter into a Metadata object.
        """

        metadata = Metadata()

        text = text.lstrip()

        if not text.startswith("---"):
            return metadata

        lines = text.splitlines()

        yaml_lines: list[str] = []

        inside_yaml = False

        for line in lines:

            if line.strip() == "---":

                if inside_yaml:
                    break

                inside_yaml = True
                continue

            if inside_yaml:
                yaml_lines.append(line.rstrip())

        current_list: str | None = None

        for line in yaml_lines:

            if not line.strip():
                continue

            # ------------------------------------------------
            # List item
            # ------------------------------------------------

            if line.startswith("  - "):

                if current_list:

                    getattr(
                        metadata,
                        current_list,
                    ).append(
                        line[4:].strip()
                    )

                continue

            current_list = None

            # ------------------------------------------------
            # Key : Value
            # ------------------------------------------------

            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = key.strip()
            value = value.strip()

            if not hasattr(metadata, key):
                continue

            attribute = getattr(metadata, key)

            if isinstance(attribute, list):

                current_list = key

                if value == "[]":
                    continue

            else:

                setattr(metadata, key, value)

        return metadata

    # ========================================================
    # Serialize
    # ========================================================

    def serialize(
        self,
        metadata: Metadata,
    ) -> str:
        """
        Serialize Metadata into YAML.
        """

        def write_list(values: list[str]) -> str:

            if not values:
                return "[]"

            return "\n" + "\n".join(
                f"  - {item}"
                for item in values
            )

        return (
            "---\n"
            f"title: {metadata.title}\n"
            f"description: {metadata.description}\n"
            f"category: {metadata.category}\n"
            f"subcategory: {metadata.subcategory}\n"
            f"difficulty: {metadata.difficulty}\n"
            f"tags: {write_list(metadata.tags)}\n"
            f"systems: {write_list(metadata.systems)}\n"
            f"aliases: {write_list(metadata.aliases)}\n"
            f"acronyms: {write_list(metadata.acronyms)}\n"
            f"references: {write_list(metadata.references)}\n"
            f"last_updated: {metadata.last_updated}\n"
            f"status: {metadata.status}\n"
            "---\n"
        )
