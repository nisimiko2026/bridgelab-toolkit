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
    selected_ordering_changed: int
    selected_top_set_changed: int
    nonselected_ordering_changed: int
    nonselected_top_set_changed: int
    maximum_top_set_difference: int


@dataclass(frozen=True, slots=True)
class TagGroupImpact:
    tag: str
    canonical_tag: str
    selected_files: int
    sharing_pairs: int
    top_ten_contributions: int
    nonselected_articles: int
    subcategories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CategoryImpactReport:
    scope: str
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
    tag_groups: tuple[TagGroupImpact, ...]
    category_pairs_changed: int
    category_pairs_added: int
    category_pairs_removed: int
    category_only_ranking: RankingImpact
    category_and_removal_ranking: RankingImpact
    reconciled_ranking: RankingImpact
    tag_reconciliation_ranking: RankingImpact
    stale_tag_removal_ranking: RankingImpact
    canonical_tag_addition_ranking: RankingImpact
    largest_ranking_impacts: tuple[tuple[str, int, int], ...]
    tag_pair_scores_increased: int
    tag_pair_scores_decreased: int
    h3_tag_pairs_increased: int
    h3_tag_pairs_decreased: int
    category_edges_before: int
    category_edges_after: int
    category_edges_added: int
    category_edges_removed: int
    relationship_articles_affected: int
    selected_relationship_articles_affected: int
    nonselected_relationship_articles_affected: int
    edges_selected_to_existing: int
    edges_existing_to_selected: int
    edges_selected_to_selected: int
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


def analyze_category_impact(
    articles: list[Article], scope: str = "all"
) -> CategoryImpactReport:
    """Project the reviewed category and tag changes without mutating input."""

    selected = _select(articles, scope)
    category_projection = project_category_impact(articles, scope, "keep")
    removal_projection = project_category_impact(articles, scope, "remove")
    reconciled_projection = project_category_impact(articles, scope, "replace")
    selected_by_id = {article.id: proposed for article, proposed in selected}
    selected_ids = set(selected_by_id)

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

    before_categories = Counter(a.metadata.category for a in articles)
    after_categories = Counter(a.metadata.category for a in category_projection)
    pair_changed, pair_added, pair_removed = _category_pair_impact(
        articles, category_projection
    )
    current_rankings = _rankings(articles)
    category_rankings = _rankings(category_projection)
    removal_rankings = _rankings(removal_projection)
    reconciled_rankings = _rankings(reconciled_projection)
    category_ranking = _ranking_impact(
        current_rankings, category_rankings, selected_ids
    )
    reconciled_ranking = _ranking_impact(
        current_rankings, reconciled_rankings, selected_ids
    )
    tag_ranking = _ranking_impact(
        category_rankings, reconciled_rankings, selected_ids
    )
    removal_ranking = _ranking_impact(
        current_rankings, removal_rankings, selected_ids
    )
    removal_increment = _ranking_impact(
        category_rankings, removal_rankings, selected_ids
    )
    addition_ranking = _ranking_impact(
        removal_rankings, reconciled_rankings, selected_ids
    )
    largest = _largest_ranking_impacts(current_rankings, category_rankings)
    _, tag_decreased = _tag_pair_impact(category_projection, removal_projection)
    tag_increased, _ = _tag_pair_impact(removal_projection, reconciled_projection)
    h3_tag_increased, h3_tag_decreased = _tag_pair_impact(
        articles, reconciled_projection
    )

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
    selected_relationship_articles = affected_relationship_articles & selected_ids
    nonselected_relationship_articles = affected_relationship_articles - selected_ids
    selected_to_existing = sum(
        source in selected_ids and target not in selected_ids for source, target in added_edges
    )
    existing_to_selected = sum(
        source not in selected_ids and target in selected_ids for source, target in added_edges
    )
    selected_to_selected = sum(
        source in selected_ids and target in selected_ids for source, target in added_edges
    )

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
        scope=scope,
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
        tag_groups=_tag_group_impacts(articles, items, current_rankings),
        category_pairs_changed=pair_changed,
        category_pairs_added=pair_added,
        category_pairs_removed=pair_removed,
        category_only_ranking=category_ranking,
        category_and_removal_ranking=removal_ranking,
        reconciled_ranking=reconciled_ranking,
        tag_reconciliation_ranking=tag_ranking,
        stale_tag_removal_ranking=removal_increment,
        canonical_tag_addition_ranking=addition_ranking,
        largest_ranking_impacts=largest,
        tag_pair_scores_increased=tag_increased,
        tag_pair_scores_decreased=tag_decreased,
        h3_tag_pairs_increased=h3_tag_increased,
        h3_tag_pairs_decreased=h3_tag_decreased,
        category_edges_before=len(before_edges),
        category_edges_after=len(after_edges),
        category_edges_added=len(added_edges),
        category_edges_removed=len(removed_edges),
        relationship_articles_affected=len(affected_relationship_articles),
        selected_relationship_articles_affected=len(selected_relationship_articles),
        nonselected_relationship_articles_affected=len(
            nonselected_relationship_articles
        ),
        edges_selected_to_existing=selected_to_existing,
        edges_existing_to_selected=existing_to_selected,
        edges_selected_to_selected=selected_to_selected,
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


def project_category_impact(
    articles: list[Article], scope: str, tag_policy: str
) -> list[Article]:
    """Return a deep-copied H1/H2/H3 projection for tests and analysis."""

    if tag_policy not in {"keep", "remove", "replace"}:
        raise ValueError(f"Unsupported category impact tag policy: {tag_policy}")
    selected = {article.id: proposed for article, proposed in _select(articles, scope)}
    projected = copy.deepcopy(articles)
    for article in projected:
        proposed = selected.get(article.id)
        if not proposed:
            continue
        old_tag = article.metadata.category.casefold()
        article.metadata.category = proposed
        if tag_policy == "keep":
            continue
        article.metadata.tags = [tag for tag in article.metadata.tags if tag != old_tag]
        if tag_policy == "replace" and proposed not in article.metadata.tags:
            article.metadata.tags.append(proposed)
    return projected


def _select(articles: list[Article], scope: str) -> list[tuple[Article, str]]:
    if scope not in {"all", "bidding", "play"}:
        raise ValueError(f"Unsupported category impact scope: {scope}")
    selected = []
    for article in articles:
        parts = article.relative_path.parts
        proposed = parts[0] if parts and parts[0] in {"bidding", "play"} else ""
        category = article.metadata.category
        if proposed and (scope == "all" or proposed == scope) and _is_structural(category):
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
    selected_ids: set[str],
) -> RankingImpact:
    ordering = top_set = selected_ordering = selected_set = maximum = 0
    for article_id in before:
        before_ids = tuple(item[0] for item in before[article_id])
        after_ids = tuple(item[0] for item in after[article_id])
        order_changed = before_ids != after_ids
        set_difference = len(set(before_ids) ^ set(after_ids))
        set_changed = bool(set_difference)
        ordering += order_changed
        top_set += set_changed
        maximum = max(maximum, set_difference)
        if article_id in selected_ids:
            selected_ordering += order_changed
            selected_set += set_changed
    return RankingImpact(
        ordering_changed=ordering,
        top_set_changed=top_set,
        selected_ordering_changed=selected_ordering,
        selected_top_set_changed=selected_set,
        nonselected_ordering_changed=ordering - selected_ordering,
        nonselected_top_set_changed=top_set - selected_set,
        maximum_top_set_difference=maximum,
    )


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


def _tag_group_impacts(
    articles: list[Article],
    items: list[CategoryImpactItem],
    rankings: dict[str, tuple[tuple[str, int], ...]],
) -> tuple[TagGroupImpact, ...]:
    article_by_id = {article.id: article for article in articles}
    selected_paths = {item.path for item in items}
    rows = []
    for tag, canonical in sorted({(item.old_tag, item.proposed_category) for item in items}):
        selected = [item for item in items if item.old_tag == tag]
        users = [article for article in articles if tag in article.metadata.tags]
        sharing_pairs = len(users) * (len(users) - 1) // 2
        contributions = 0
        for source, ranked in rankings.items():
            source_tags = article_by_id[source].metadata.tags
            if tag not in source_tags:
                continue
            contributions += sum(
                tag in article_by_id[target].metadata.tags for target, _ in ranked
            )
        nonselected = sum(
            article.relative_path.as_posix() not in selected_paths for article in users
        )
        rows.append(
            TagGroupImpact(
                tag=tag,
                canonical_tag=canonical,
                selected_files=len(selected),
                sharing_pairs=sharing_pairs,
                top_ten_contributions=contributions,
                nonselected_articles=nonselected,
                subcategories=tuple(sorted({item.subcategory for item in selected})),
            )
        )
    return tuple(rows)
