"""
BridgeLab Toolkit
Cross-Reference Writer
"""

from __future__ import annotations

from core.models import CrossReference


class CrossReferenceWriter:
    """
    Converts CrossReference objects into Markdown.
    """

    # ---------------------------------------------------------

    def write(
        self,
        reference: CrossReference,
    ) -> str:

        lines = []

        lines.append("# Related BridgeLab Articles")

        # -----------------------------------------------------
        # Prerequisites
        # -----------------------------------------------------

        if reference.prerequisites:

            lines.append("")
            lines.append("## Prerequisites")
            lines.append("")

            for item in reference.prerequisites:

                lines.append(f"- {item.article}")

        # -----------------------------------------------------
        # Related Topics
        # -----------------------------------------------------

        if reference.related_topics:

            lines.append("")
            lines.append("## Related Topics")
            lines.append("")

            for item in reference.related_topics:

                lines.append(f"- {item.article}")

        # -----------------------------------------------------
        # Related Systems
        # -----------------------------------------------------

        if reference.related_systems:

            lines.append("")
            lines.append("## Related Systems")
            lines.append("")

            for item in reference.related_systems:

                lines.append(f"- {item.article}")

        # -----------------------------------------------------
        # Advanced Topics
        # -----------------------------------------------------

        if reference.advanced_topics:

            lines.append("")
            lines.append("## Advanced Topics")
            lines.append("")

            for item in reference.advanced_topics:

                lines.append(f"- {item.article}")

        return "\n".join(lines)
