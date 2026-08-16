"""Generate reviewable proposals for missing article metadata."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from core.models import Article
from metadata.validator import MetadataValidator


@dataclass(frozen=True, slots=True)
class RepairProposal:
    article: str
    field: str
    current: str
    proposed: str
    confidence: str
    rationale: str


class MetadataRepairPlanner:
    """Build deterministic suggestions without modifying source articles."""

    FRONT_MATTER_RE = re.compile(
        r"\A(?:\ufeff)?---[ \t]*(?:\r\n|\n).*?(?:\r\n|\n)---[ \t]*(?:\r\n|\n)",
        re.DOTALL,
    )
    LINK_RE = re.compile(r"!?\[([^]]*)\]\([^)]*\)")
    MARKUP_RE = re.compile(r"[`*_~]+")

    def build(self, articles: list[Article]) -> list[RepairProposal]:
        directory_levels: dict[Path, list[str]] = defaultdict(list)
        ancestor_levels: dict[Path, list[str]] = defaultdict(list)
        category_levels: dict[str, list[str]] = defaultdict(list)

        for article in articles:
            level = article.metadata.difficulty
            if level and MetadataValidator._is_valid_difficulty(level):
                directory_levels[article.relative_path.parent].append(level)
                for parent in article.relative_path.parents:
                    ancestor_levels[parent].append(level)
                if article.metadata.category:
                    category_levels[article.metadata.category].append(level)

        proposals: list[RepairProposal] = []

        for article in sorted(articles, key=lambda item: item.relative_path.as_posix()):
            subject = article.relative_path.as_posix()

            if not article.metadata.description:
                proposed, confidence, rationale = self._description(article)
                proposals.append(
                    RepairProposal(
                        article=subject,
                        field="description",
                        current="",
                        proposed=proposed,
                        confidence=confidence,
                        rationale=rationale,
                    )
                )

            if (
                not article.metadata.difficulty
                and MetadataValidator._requires_difficulty(article)
            ):
                proposed, confidence, rationale = self._difficulty(
                    article,
                    directory_levels,
                    ancestor_levels,
                    category_levels,
                )
                proposals.append(
                    RepairProposal(
                        article=subject,
                        field="difficulty",
                        current="",
                        proposed=proposed,
                        confidence=confidence,
                        rationale=rationale,
                    )
                )

        return proposals

    def export(
        self,
        proposals: list[RepairProposal],
        json_output: Path,
        markdown_output: Path,
    ) -> None:
        """Write deterministic JSON and Markdown review artifacts."""

        json_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.parent.mkdir(parents=True, exist_ok=True)

        counts = Counter(proposal.field for proposal in proposals)
        data = {
            "summary": {
                "total_proposals": len(proposals),
                "descriptions": counts["description"],
                "difficulties": counts["difficulty"],
            },
            "proposals": [asdict(proposal) for proposal in proposals],
        }
        json_output.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        lines = [
            "# Metadata Repair Plan",
            "",
            f"- Total proposals: {len(proposals)}",
            f"- Missing descriptions: {counts['description']}",
            f"- Missing difficulties: {counts['difficulty']}",
            "- Source files modified: 0",
            "",
        ]

        for proposal in proposals:
            lines.extend(
                [
                    f"## {proposal.article} — {proposal.field}",
                    "",
                    f"- Proposed: {proposal.proposed or '[manual review required]'}",
                    f"- Confidence: {proposal.confidence}",
                    f"- Rationale: {proposal.rationale}",
                    "",
                ]
            )

        markdown_output.write_text("\n".join(lines), encoding="utf-8")

    @classmethod
    def _description(cls, article: Article) -> tuple[str, str, str]:
        try:
            text = article.path.read_text(encoding="utf-8")
        except OSError:
            return "", "none", "Article could not be read."

        text = cls.FRONT_MATTER_RE.sub("", text, count=1)
        paragraphs = re.split(r"(?:\r?\n){2,}", text)

        for paragraph in paragraphs:
            lines = [line.strip() for line in paragraph.splitlines()]
            if not lines or any(line.startswith("#") for line in lines):
                continue
            if all(
                not line
                or line.startswith(("- ", "* ", ">", "|", "```"))
                for line in lines
            ):
                continue

            candidate = " ".join(line for line in lines if line)
            candidate = cls.LINK_RE.sub(r"\1", candidate)
            candidate = cls.MARKUP_RE.sub("", candidate)
            candidate = re.sub(r"\s+", " ", candidate).strip()

            if len(candidate) >= MetadataValidator.MIN_DESCRIPTION_LENGTH:
                return (
                    candidate,
                    "medium",
                    "Derived from the first substantive prose paragraph.",
                )

        return "", "none", "No suitable prose paragraph was found."

    @staticmethod
    def _mode(values: list[str]) -> tuple[str, int, bool]:
        if not values:
            return "", 0, False
        counts = Counter(values)
        ranked = counts.most_common()
        tied = len(ranked) > 1 and ranked[0][1] == ranked[1][1]
        return ranked[0][0], ranked[0][1], tied

    @classmethod
    def _difficulty(
        cls,
        article: Article,
        directory_levels: dict[Path, list[str]],
        ancestor_levels: dict[Path, list[str]],
        category_levels: dict[str, list[str]],
    ) -> tuple[str, str, str]:
        peers = directory_levels.get(article.relative_path.parent, [])
        value, occurrences, tied = cls._mode(peers)

        if value and not tied:
            confidence = "high" if occurrences >= 3 else "medium"
            return (
                value,
                confidence,
                f"Most common difficulty among {len(peers)} article(s) in the same directory.",
            )

        if "index" in article.relative_path.name.casefold():
            return (
                "All Levels",
                "medium",
                "Index documents are intended to serve readers at all levels.",
            )

        for parent in article.relative_path.parents:
            peers = ancestor_levels.get(parent, [])
            value, occurrences, tied = cls._mode(peers)
            if value and not tied:
                return (
                    value,
                    "low",
                    f"Most common difficulty among {len(peers)} article(s) under '{parent.as_posix()}'.",
                )

        category = article.metadata.category
        category_peers = category_levels.get(category, [])
        value, _, tied = cls._mode(category_peers)

        if value and not tied:
            return (
                value,
                "low",
                f"Most common difficulty in category '{category}'.",
            )

        return "", "none", "No unambiguous peer difficulty was available."
