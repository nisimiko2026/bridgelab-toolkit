"""
BridgeLab Toolkit
Metadata Writer
"""

from __future__ import annotations

from core.models import Article, Metadata
from enrichment.generator import MetadataGenerator
from enrichment.parser import MetadataParser


# ============================================================
# Metadata Writer
# ============================================================

class MetadataWriter:
    """
    Enrich metadata in Markdown articles.
    """

    def __init__(self) -> None:

        self.generator = MetadataGenerator()
        self.parser = MetadataParser()

    # ========================================================
    # Write
    # ========================================================

    def write(
        self,
        article: Article,
    ) -> bool:
        """
        Update metadata for one article.

        Returns True if the file was modified.
        """

        text = article.path.read_text(encoding="utf-8")

        current = self.parser.parse(text)

        generated = self.generator.generate(article)

        changed = self.merge(
            current=current,
            generated=generated,
        )

        if not changed:
            return False

        yaml = self.parser.serialize(current)

        body = self._body(text)

        article.path.write_text(
            yaml + "\n" + body,
            encoding="utf-8",
        )

        return True

    # ========================================================
    # Merge
    # ========================================================

    def merge(
        self,
        current: Metadata,
        generated: Metadata,
    ) -> bool:
        """
        Fill only empty metadata fields.

        Returns True if anything changed.
        """

        changed = False

        for field in current.__dataclass_fields__:

            current_value = getattr(current, field)
            generated_value = getattr(generated, field)

            if isinstance(current_value, list):

                if not current_value and generated_value:

                    setattr(current, field, generated_value)

                    changed = True

            else:

                if (
                    not current_value
                    and generated_value
                ):

                    setattr(current, field, generated_value)

                    changed = True

        return changed

    # ========================================================
    # Body
    # ========================================================

    def _body(
        self,
        text: str,
    ) -> str:
        """
        Return Markdown body without YAML front matter.
        """

        text = text.lstrip()

        if not text.startswith("---"):
            return text

        lines = text.splitlines()

        end = None

        count = 0

        for i, line in enumerate(lines):

            if line.strip() == "---":

                count += 1

                if count == 2:

                    end = i

                    break

        if end is None:
            return text

        return "\n".join(lines[end + 1 :]).lstrip()
