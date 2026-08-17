"""Read-only impact analysis for reviewed structural category metadata."""

from __future__ import annotations

import copy
from collections import Counter
from dataclasses import dataclass

from analysis.graph import KnowledgeGraph
from analysis.orphans import OrphanAnalyzer
from analysis.related import RelatedAnalyzer
from core.models import Article
from metadata.repair_plan import MetadataRepairPlanner
from metadata.validator import MetadataValidator
from relationships.analyzer import RelationshipAnalyzer


@dataclass(frozen=True, slots=True)
class CategoryImpactItem:
    path: str
    current_category: str
    proposed_category: str
    subcategory: str
    old_tag: str
    old_tag_present: bool
    canonical_tag_present: bool

    @property
    def tag_action(self) -> str:
        if self.old_tag_present and not self.canonical_tag_present:
            return "remove old derived tag; add canonical tag"
        if self.old_tag_present:
            return "remove old derived tag"
        if not self.canonical_tag_present:
            return "add canonical tag"
        return "neither"


@dataclass(frozen=True, slots=True)
class RankingImpact:
    ordering_changed: int
    top_set_changed: int


@dataclass(frozen=True, slots=True)
class CategoryImpactReport:
    items: tuple[CategoryImpactItem, ...]
    article_count: int
    distinct_categories_before: int
    distinct_categories_after: int
    bidding_before: int
    bidding_after: int
    play_before: int
    play_after: int
    structural_findings_eliminated: int
    provisional_findings_affected: int
    path_disagreements_affected: int
    old_tags_present: int
    canonical_tags_present: int
    stale_tags: int
    canonical_tags_to_add: int
    duplicate_tag_risk: int
    structural_tag_findings_eliminated: int
    tag_mappings: tuple[tuple[str, str, int], ...]
    category_pairs_changed: int
    category_pairs_added: int
    category_pairs_removed: int
    category_only_ranking: RankingImpact
    reconciled_ranking: RankingImpact
    tag_reconciliation_ranking: RankingImpact
    stale_tag_removal_ranking: RankingImpact
    canonical_tag_addition_ranking: RankingImpact
    largest_ranking_impacts: tuple[tuple[str, int, int], ...]
    tag_pair_scores_increased: int
    tag_pair_scores_decreased: int
    category_edges_before: int
    category_edges_after: int
    category_edges_added: int
    category_edges_removed: int
    relationship_articles_affected: int
    crossref_candidate_sets_changed: int
    repairable_missing_difficulty: int
    repair_fallback_changes: int
    orphan_groups_before: int
    orphan_groups_after: int
    orphan_articles_regrouped: int
    orphan_bidding_before: int
    orphan_bidding_after: int
    orphan_play_before: int
    orphan_play_after: int


def analyze_category_impact(articles: list[Article]) -> CategoryImpactReport:
    """Project the reviewed category and tag changes without mutating input."""

    selected = _select(articles)
    category_projection = copy.deepcopy(articles)
    removal_projection = copy.deepcopy(articles)
    reconciled_projection = copy.deepcopy(articles)
    selected_by_id = {article.id: proposed for article, proposed in selected}

    items: list[CategoryImpactItem] = []
    tag_mappings: Counter[tuple[str, str]] = Counter()
    for article, proposed in selected:
        old_tag = article.metadata.category.casefold()
        tags = article.metadata.tags
        old_present = old_tag in tags
        canonical_present = proposed in tags
        items.append(
            CategoryImpactItem(
                path=article.relative_path.as_posix(),
                current_category=article.metadata.category,
                proposed_category=proposed,
                subcategory=article.metadata.subcategory,
                old_tag=old_tag,
                old_tag_present=old_present,
                canonical_tag_present=canonical_present,
            )
        )
        tag_mappings[(old_tag, proposed)] += 1

    for article in category_projection:
        proposed = selected_by_id.get(article.id)
        if proposed:
            article.metadata.category = proposed

    for article in reconciled_projection:
        proposed = selected_by_id.get(article.id)
        if not proposed:
            continue
        old_tag = article.metadata.category.casefold()
        article.metadata.category = proposed
        article.metadata.tags = [tag for tag in article.metadata.tags if tag != old_tag]
        if proposed not in article.metadata.tags:
            article.metadata.tags.append(proposed)

    for article in removal_projection:
        proposed = selected_by_id.get(article.id)
        if not proposed:
            continue
        old_tag = article.metadata.category.casefold()
        article.metadata.category = proposed
        article.metadata.tags = [tag for tag in article.metadata.tags if tag != old_tag]

    before_categories = Counter(a.metadata.category for a in articles)
    after_categories = Counter(a.metadata.category for a in category_projection)
    pair_changed, pair_added, pair_removed = _category_pair_impact(
        articles, category_projection
    )
    current_rankings = _rankings(articles)
    category_rankings = _rankings(category_projection)
    removal_rankings = _rankings(removal_projection)
    reconciled_rankings = _rankings(reconciled_projection)
    category_ranking = _ranking_impact(current_rankings, category_rankings)
    reconciled_ranking = _ranking_impact(current_rankings, reconciled_rankings)
    tag_ranking = _ranking_impact(category_rankings, reconciled_rankings)
    removal_ranking = _ranking_impact(category_rankings, removal_rankings)
    addition_ranking = _ranking_impact(removal_rankings, reconciled_rankings)
    largest = _largest_ranking_impacts(current_rankings, reconciled_rankings)
    _, tag_decreased = _tag_pair_impact(category_projection, removal_projection)
    tag_increased, _ = _tag_pair_impact(removal_projection, reconciled_projection)

    before_edges = _category_edges(articles)
    after_edges = _category_edges(category_projection)
    added_edges = after_edges - before_edges
    removed_edges = before_edges - after_edges
    affected_relationship_articles = {
        node for edge in added_edges | removed_edges for node in edge
    }
    changed_crossref_sources = {
        source for source, _ in added_edges | removed_edges
    }

    before_orphans = _orphan_groups(articles)
    after_orphans = _orphan_groups(category_projection)
    before_orphan_category = _orphan_category_by_id(articles)
    after_orphan_category = _orphan_category_by_id(category_projection)
    regrouped = sum(
        before_orphan_category.get(article_id) != category
        for article_id, category in after_orphan_category.items()
        if article_id in before_orphan_category
    )

    missing = [
        article
        for article in articles
        if not article.metadata.difficulty
        and MetadataValidator._requires_difficulty(article)
    ]
    before_repairs = _difficulty_repairs(articles)
    after_repairs = _difficulty_repairs(category_projection)
    repair_changes = sum(
        before_repairs.get(path) != after_repairs.get(path)
        for path in set(before_repairs) | set(after_repairs)
    )

    return CategoryImpactReport(
        items=tuple(sorted(items, key=lambda item: item.path.casefold())),
        article_count=len(articles),
        distinct_categories_before=len(before_categories),
        distinct_categories_after=len(after_categories),
        bidding_before=before_categories["bidding"],
        bidding_after=after_categories["bidding"],
        play_before=before_categories["play"],
        play_after=after_categories["play"],
        structural_findings_eliminated=len(items),
        provisional_findings_affected=len(items),
        path_disagreements_affected=0,
        old_tags_present=sum(item.old_tag_present for item in items),
        canonical_tags_present=sum(item.canonical_tag_present for item in items),
        stale_tags=sum(item.old_tag_present for item in items),
        canonical_tags_to_add=sum(not item.canonical_tag_present for item in items),
        duplicate_tag_risk=sum(
            item.old_tag_present and item.canonical_tag_present for item in items
        ),
        structural_tag_findings_eliminated=sum(item.old_tag_present for item in items),
        tag_mappings=tuple(
            (old, new, count)
            for (old, new), count in sorted(tag_mappings.items())
        ),
        category_pairs_changed=pair_changed,
        category_pairs_added=pair_added,
        category_pairs_removed=pair_removed,
        category_only_ranking=category_ranking,
        reconciled_ranking=reconciled_ranking,
        tag_reconciliation_ranking=tag_ranking,
        stale_tag_removal_ranking=removal_ranking,
        canonical_tag_addition_ranking=addition_ranking,
        largest_ranking_impacts=largest,
        tag_pair_scores_increased=tag_increased,
        tag_pair_scores_decreased=tag_decreased,
        category_edges_before=len(before_edges),
        category_edges_after=len(after_edges),
        category_edges_added=len(added_edges),
        category_edges_removed=len(removed_edges),
        relationship_articles_affected=len(affected_relationship_articles),
        crossref_candidate_sets_changed=len(changed_crossref_sources),
        repairable_missing_difficulty=len(missing),
        repair_fallback_changes=repair_changes,
        orphan_groups_before=len(before_orphans),
        orphan_groups_after=len(after_orphans),
        orphan_articles_regrouped=regrouped,
        orphan_bidding_before=before_orphans.get("bidding", 0),
        orphan_bidding_after=after_orphans.get("bidding", 0),
        orphan_play_before=before_orphans.get("play", 0),
        orphan_play_after=after_orphans.get("play", 0),
    )


def _select(articles: list[Article]) -> list[tuple[Article, str]]:
    selected = []
    for article in articles:
        parts = article.relative_path.parts
        proposed = parts[0] if parts and parts[0] in {"bidding", "play"} else ""
        category = article.metadata.category
        if proposed and _is_structural(category):
            selected.append((article, proposed))
    return sorted(selected, key=lambda item: item[0].relative_path.as_posix().casefold())


def _is_structural(value: str) -> bool:
    return "/" in value or " – " in value or " — " in value


def _rankings(articles: list[Article]) -> dict[str, tuple[tuple[str, int], ...]]:
    analyzer = RelatedAnalyzer(KnowledgeGraph(articles))
    return {
        article.id: tuple((candidate.id, score) for candidate, score in analyzer.related(article))
        for article in articles
    }


def _ranking_impact(
    before: dict[str, tuple[tuple[str, int], ...]],
    after: dict[str, tuple[tuple[str, int], ...]],
) -> RankingImpact:
    ordering = 0
    top_set = 0
    for article_id in before:
        before_ids = tuple(item[0] for item in before[article_id])
        after_ids = tuple(item[0] for item in after[article_id])
        ordering += before_ids != after_ids
        top_set += set(before_ids) != set(after_ids)
    return RankingImpact(ordering_changed=ordering, top_set_changed=top_set)


def _largest_ranking_impacts(
    before: dict[str, tuple[tuple[str, int], ...]],
    after: dict[str, tuple[tuple[str, int], ...]],
) -> tuple[tuple[str, int, int], ...]:
    rows = []
    for article_id in before:
        before_ids = {item[0] for item in before[article_id]}
        after_ids = {item[0] for item in after[article_id]}
        changed = len(before_ids ^ after_ids)
        score_delta = sum(score for _, score in after[article_id]) - sum(
            score for _, score in before[article_id]
        )
        if changed or score_delta:
            rows.append((article_id, changed, score_delta))
    return tuple(sorted(rows, key=lambda row: (-row[1], -abs(row[2]), row[0]))[:10])


def _category_pair_impact(
    before: list[Article], after: list[Article]
) -> tuple[int, int, int]:
    changed = added = removed = 0
    for index, left in enumerate(before):
        for offset, right in enumerate(before[index + 1 :], start=index + 1):
            old_match = bool(left.metadata.category) and (
                left.metadata.category == right.metadata.category
            )
            new_match = bool(after[index].metadata.category) and (
                after[index].metadata.category == after[offset].metadata.category
            )
            if old_match != new_match:
                changed += 1
                added += new_match
                removed += old_match
    return changed, added, removed


def _tag_pair_impact(before: list[Article], after: list[Article]) -> tuple[int, int]:
    increased = decreased = 0
    for index, left in enumerate(before):
        for offset, right in enumerate(before[index + 1 :], start=index + 1):
            old_shared = len(set(left.metadata.tags) & set(right.metadata.tags))
            new_shared = len(
                set(after[index].metadata.tags) & set(after[offset].metadata.tags)
            )
            increased += new_shared > old_shared
            decreased += new_shared < old_shared
    return increased, decreased


def _category_edges(articles: list[Article]) -> set[tuple[str, str]]:
    return {
        (relationship.source, relationship.target)
        for relationship in RelationshipAnalyzer().analyze(articles)
        if relationship.relation == "category"
    }


def _orphan_groups(articles: list[Article]) -> dict[str, int]:
    return OrphanAnalyzer(KnowledgeGraph(articles)).summary()


def _orphan_category_by_id(articles: list[Article]) -> dict[str, str]:
    analyzer = OrphanAnalyzer(KnowledgeGraph(articles))
    return {article.id: article.metadata.category for article in analyzer.articles()}


def _difficulty_repairs(articles: list[Article]) -> dict[str, tuple[str, str, str]]:
    return {
        proposal.article: (
            proposal.proposed,
            proposal.confidence,
            proposal.rationale,
        )
        for proposal in MetadataRepairPlanner().build(articles)
        if proposal.field == "difficulty"
    }
