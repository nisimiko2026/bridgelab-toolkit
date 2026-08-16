from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from core.models import Article

from .graph import KnowledgeGraph


@dataclass(frozen=True, slots=True)
class OrphanProposal:
    target: str
    parent_index: str | None
    confidence: str
    reason: str
    candidates: tuple[str, ...] = ()


class OrphanRepairPlanner:
    """Propose parent-index references for articles with no inbound links."""

    def build(self, articles: list[Article]) -> list[OrphanProposal]:
        graph = KnowledgeGraph(articles)
        indexes = [article for article in articles if "index" in article.filename]

        proposals = [
            self._proposal(article, indexes)
            for article in graph.orphan_articles()
        ]
        return sorted(proposals, key=lambda proposal: proposal.target)

    def _proposal(
        self,
        article: Article,
        indexes: list[Article],
    ) -> OrphanProposal:
        directory = article.relative_path.parent

        while directory != Path("."):
            candidates = sorted(
                (
                    item for item in indexes
                    if item.relative_path.parent == directory
                    and item.id != article.id
                ),
                key=lambda item: item.id,
            )

            if len(candidates) == 1:
                same_directory = directory == article.relative_path.parent
                return OrphanProposal(
                    target=article.id,
                    parent_index=candidates[0].id,
                    confidence="high" if same_directory else "medium",
                    reason=(
                        "single index in target directory"
                        if same_directory
                        else "single index in nearest ancestor directory"
                    ),
                )
            if len(candidates) > 1:
                return OrphanProposal(
                    target=article.id,
                    parent_index=None,
                    confidence="manual",
                    reason="multiple candidate indexes",
                    candidates=tuple(item.id for item in candidates),
                )

            directory = directory.parent

        return OrphanProposal(
            target=article.id,
            parent_index=None,
            confidence="manual",
            reason="no parent index found",
        )

    def export(
        self,
        proposals: list[OrphanProposal],
        json_output: Path,
        markdown_output: Path,
    ) -> None:
        actionable = sum(item.parent_index is not None for item in proposals)
        summary = {
            "total_candidates": len(proposals),
            "actionable": actionable,
            "manual_review": len(proposals) - actionable,
            "high_confidence": sum(item.confidence == "high" for item in proposals),
            "medium_confidence": sum(
                item.confidence == "medium" for item in proposals
            ),
        }
        data = {
            "summary": summary,
            "proposals": [asdict(item) for item in proposals],
        }
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        lines = [
            "# Orphan Repair Plan",
            "",
            f"- Total candidates: {summary['total_candidates']}",
            f"- Actionable proposals: {summary['actionable']}",
            f"- Manual review: {summary['manual_review']}",
            "",
            "| Target | Proposed parent index | Confidence | Reason |",
            "|---|---|---|---|",
        ]
        for item in proposals:
            parent = item.parent_index or ", ".join(item.candidates) or "—"
            lines.append(
                f"| `{item.target}` | `{parent}` | {item.confidence} | {item.reason} |"
            )
        markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
