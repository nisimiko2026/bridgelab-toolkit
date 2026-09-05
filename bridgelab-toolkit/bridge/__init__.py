"""BridgeLab Bridge Engine domain foundation."""
# ruff: noqa: F401 -- this package module intentionally re-exports its imports

from .auction import (
    Auction, AuctionEntry, Bid, Call, CallType, Contract, Doubling, Strain,
)
from .bidding_engine import BiddingEngine, BiddingEngineResult
from .bidding_rules import (
    BiddingContext, BiddingRule, KnowledgeSource, RuleDecision, SystemContext, evaluate_rule,
)
from .evaluation import (
    HandEvaluation, ShapeClass, SuitHonorEvidence, SuitQualityEvidence, all_suit_honor_evidence,
    classify_shape, controls, distribution, evaluate_hand, high_card_points,
    suit_honor_evidence, suit_lengths, suit_quality_evidence, all_suit_quality_evidence,
)
from .models import Card, Hand, Rank, Seat, Suit, Vulnerability

__all__ = [
    "Auction", "AuctionEntry", "Bid", "BiddingContext", "BiddingEngine", "BiddingEngineResult", "BiddingRule", "Call",
    "CallType", "Card", "Contract", "Doubling", "Hand", "HandEvaluation",
    "KnowledgeSource", "Rank", "RuleDecision", "Seat", "ShapeClass", "Strain",
    "StopperAssessment", "StopperPolicy", "StopperStatus", "OffensiveHandAssessment", "OffensiveHandPolicy", "OffensiveHandStatus", "PlayingStrengthAssessment", "PlayingStrengthPolicy", "PlayingStrengthStatus", "Suit", "SuitHonorEvidence", "SuitQualityEvidence", "SystemContext", "Vulnerability", "all_suit_honor_evidence", "all_suit_quality_evidence", "classify_shape", "controls",
    "distribution", "evaluate_hand", "evaluate_rule", "high_card_points",
    "assess_stopper", "assess_suit_quality", "assess_playing_strength", "assess_offensive_hand", "SuitQualityAssessment", "SuitQualityPolicy", "SuitQualityStatus", "suit_honor_evidence", "suit_quality_evidence", "suit_lengths",
]


from .sayc import (
    SaycOneClubOpeningRule,
    SaycOneDiamondOpeningRule,
    SaycOneHeartOpeningRule,
    SaycOneNotrumpOpeningRule,
    SaycOneSpadeOpeningRule,
    create_sayc_opening_engine,
    sayc_opening_rules,
)


from .sayc_responses import (
    SaycResponseToOneClubOneDiamondRule,
    SaycResponseToOneClubOneHeartRule,
    SaycResponseToOneClubOneSpadeRule,
    SaycResponseToOneClubPassRule,
    create_sayc_one_club_response_engine,
    sayc_one_club_response_rules,
)


from .sayc_1d_responses import (
    SaycResponseToOneDiamondOneHeartRule,
    SaycResponseToOneDiamondOneSpadeRule,
    SaycResponseToOneDiamondPassRule,
    create_sayc_one_diamond_response_engine,
    sayc_one_diamond_response_rules,
)


from .stopper_policy import (
    StopperAssessment,
    StopperPolicy,
    StopperStatus,
    assess_stopper,
)


from .policy_registry import (
    STOPPER_POLICY_OPTION,
    SUIT_QUALITY_POLICY_OPTION,
    PLAYING_STRENGTH_POLICY_OPTION,
    OFFENSIVE_HAND_POLICY_OPTION,
    PolicyRegistry,
    assess_configured_stopper,
    assess_configured_suit_quality,
    assess_configured_playing_strength,
    assess_configured_offensive_hand,
    configured_stopper_policy_id,
    configured_suit_quality_policy_id,
    configured_playing_strength_policy_id,
    configured_offensive_hand_policy_id,
    resolve_stopper_policy,
    resolve_suit_quality_policy,
    resolve_playing_strength_policy,
    resolve_offensive_hand_policy,
)

from .sayc_1nt_stayman_continuations import (
    SaycOneNotrumpStaymanMajorFitGameContinuationRule,
    create_sayc_one_notrump_stayman_major_fit_game_continuation_engine,
)


from .suit_quality_policy import (
    SuitQualityAssessment,
    SuitQualityPolicy,
    SuitQualityStatus,
    assess_suit_quality,
)


from .playing_strength_policy import (
    PlayingStrengthAssessment,
    PlayingStrengthPolicy,
    PlayingStrengthStatus,
    assess_playing_strength,
)
from .offensive_hand_policy import (
    OffensiveHandAssessment,
    OffensiveHandPolicy,
    OffensiveHandStatus,
    assess_offensive_hand,
)


from .two_over_one_responses import (
    create_sayc_two_over_one_response_engine,
    sayc_two_over_one_response_rules,
)

from .two_over_one import is_canonical_two_over_one_pair


from .two_over_one_opener_rebids import (
    SaycTwoOverOneOneHeartTwoDiamondTwoSpadeRule,
    SaycTwoOverOneOneSpadeTwoClubTwoDiamondRule,
    SaycTwoOverOneOneSpadeTwoClubThreeClubRule,
    SaycTwoOverOneOneSpadeTwoClubTwoSpadeRule,
    create_sayc_two_over_one_opener_rebid_engine,
    sayc_two_over_one_opener_rebid_rules,
)


from .two_over_one_balanced_rebids import (
    TwoOverOneBalancedRebidEvidence,
    assess_one_heart_two_diamond_balanced_rebid,
)


from .auction_simulation import (
    AuctionSimulationResult,
    ControlledAuctionSimulator,
    SimulationStep,
    SimulationStopReason,
)


from .engine_router import (
    BiddingEngineRouter,
    EngineRoute,
    EngineRouteMatch,
    RecommendationEngine,
    auction_calls,
)


from .sayc_route_configuration import (
    combine_existing_engines,
    create_standard_sayc_router,
)


from .deals import Deal, full_deck, generate_deal, generate_deals
from .simulation_statistics import SimulationStatistics, summarize_simulations


from .batch_simulation import (
    BatchSimulationCase,
    BatchSimulationReport,
    EngineFactory,
    SystemFactory,
    run_seeded_batch,
)

from .sayc_coverage_benchmark import SaycCoverageBenchmarkReport, SaycCoverageMetrics, run_sayc_coverage_benchmark

from .abstention_analysis import AbstentionAnalysis, AbstentionClassification, analyze_benchmark_abstentions

from .continuation_analysis import ContinuationAuctionCount, ContinuationBreakdown, continuation_breakdown

from .sayc_1d1h_opener_rebids import SaycOneDiamondOneHeartTwoHeartRule, SaycOneDiamondOneHeartOneNotrumpRule, create_sayc_one_diamond_one_heart_opener_rebid_engine

from .sayc_competitive_benchmark import (
    SaycCompetitiveBenchmarkReport,
    SaycCompetitiveMetrics,
    run_sayc_direct_overcall_benchmark,
)

from .sayc_competitive_benchmark import SaycTakeoutAdvancerBenchmarkReport, SaycTakeoutAdvancerMetrics, run_sayc_takeout_advancer_benchmark

from .sayc_competitive_benchmark import SaycDirectOneNotrumpBenchmarkReport, SaycDirectOneNotrumpMetrics, run_sayc_direct_one_notrump_benchmark

from .milestone_benchmark import MILESTONE_VERSION, DEFAULT_START_SEED, DEFAULT_DEAL_COUNT, MilestoneScenario, MilestoneResult, MilestoneSummary, SCENARIOS, validate_milestone_results, summarize_milestone

from .milestone_runner import run_phase10_milestone, run_phase10_milestone_chunked, merge_phase10_chunks

from .milestone_checkpoint import summary_to_dict, summary_from_dict, save_checkpoint, load_checkpoint, run_checkpoint, merge_checkpoint_files

from .milestone_execution import CheckpointSpec, checkpoint_plan, completed_checkpoint_specs, next_pending_checkpoint, run_next_checkpoint, merge_completed_plan

from .abstention_diagnostics import AbstentionDiagnostic, AbstentionReason, DiagnosedEngineResult, RuleRejection, evaluate_with_abstention_diagnostic

from .deal_analysis import (
    AbstentionCode, ActionKind, AnalysisAction, AnalysisEvidence, AnalysisStage,
    AnalysisStatus, DealAnalysisContext, DealAnalysisResult, Subsystem,
    SubsystemResult, analyze_deal_decision, detect_analysis_stage,
)
from .declarer_play_state import (
    DeclarerHandRole, DeclarerPlayInput, DeclarerPlayState,
    DeclarerStateBuildResult, DeclarerStateFailureCode, PlayedCard, Trick,
    build_declarer_play_state, legal_cards,
)
from .declarer_recommendation import (
    DeclarerRecommendation, DeclarerRecommendationReason,
    DeclarerRecommendationStatus, DeclarerTechnique, UNBLOCK_SOURCE,
    evaluate_declarer_play,
)
from .probability_evidence import (
    ProbabilityEvidence, ProbabilityEvidenceFailureCode,
    ProbabilityEvidenceResult, ProbabilityEvidenceStatus, ProbabilityEvidenceType,
    collect_declarer_probability_evidence,
)
from .probability_engine import (
    CalculationMode, DEFAULT_PROBABILITY_ENGINE_REGISTRY, FormulaIdentifier,
    ProbabilityContext, ProbabilityEngineFailureCode, ProbabilityEngineRegistry,
    ProbabilityEngineResult, ProbabilityEngineStatus, build_probability_context,
    evaluate_probability,
)
from .probability_questions import (
    KnownCardCountQuestion, MonteCarloQuestion, ProbabilityQuestion, RestrictedChoiceQuestion,
    SuitDistributionQuestion, TrumpBreakQuestion, VacantPlacesQuestion,
)
from .defensive_play_state import (
    DefensivePlayInput, DefensivePlayState, DefensiveStateBuildResult,
    DefensiveStateFailureCode, build_defensive_play_state,
    build_defensive_probability_context,
)
from .opening_lead_state import (
    OpeningLeadInput, OpeningLeadState, OpeningLeadStateBuildResult,
    OpeningLeadStateFailureCode, build_opening_lead_probability_context,
    build_opening_lead_state,
)
from .opening_lead_policy import (
    OpeningLeadHonorStyle, OpeningLeadLengthMethod, OpeningLeadPolicy,
    OpeningLeadPolicyAssessment, OpeningLeadTopOfNothing,
    assess_opening_lead_policy,
)
from .deal_summary import (
    DealSummaryFailureCode, DealSummaryInput, DealSummaryItem,
    DealSummaryResult, DealSummaryStatus, build_deal_summary,
)
from .deal_summary_rendering import (
    DealSummaryRenderedSection, DealSummaryRendering,
    DealSummaryRenderingStatus, render_deal_summary,
)
from .deal_summary_pipeline import (
    DealSummaryPipelineFailureCode, DealSummaryPipelineResult,
    DealSummaryPipelineStatus, build_and_render_deal_summary,
)
from .full_deal_analysis import (
    FullDealAnalysisInput, FullDealAnalysisResult, FullDealProbabilityRequest,
    FullDealSkippedStage, FullDealSkipReason, analyze_full_deal,
)
from .policy_registry import OPENING_LEAD_POLICY_OPTION


from .jacoby_continuation_strength_policy import (
    JacobyContinuationStrengthAssessment,
    JacobyContinuationStrengthClass,
    JacobyContinuationStrengthPolicy,
    assess_jacoby_continuation_strength,
)
from .policy_registry import (
    JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION,
    assess_configured_jacoby_continuation_strength,
    configured_jacoby_continuation_strength_policy_id,
    resolve_jacoby_continuation_strength_policy,
)

from .sayc_1nt_jacoby import (
    SaycOneNotrumpJacobyContinuationRule,
    create_sayc_one_notrump_jacoby_continuation_engine,
)

from .stayman_continuation_strength_policy import (
    StaymanContinuationStrength,
    StaymanContinuationStrengthAssessment,
    StaymanContinuationStrengthPolicy,
    assess_stayman_continuation_strength,
)
from .policy_registry import (
    STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION,
    assess_configured_stayman_continuation_strength,
    configured_stayman_continuation_strength_policy_id,
    resolve_stayman_continuation_strength_policy,
)
from .stayman_dual_major_response_policy import (
    StaymanDualMajorResponse,
    StaymanDualMajorResponseAssessment,
    StaymanDualMajorResponsePolicy,
    assess_stayman_dual_major_response,
)
from .policy_registry import (
    STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION,
    assess_configured_stayman_dual_major_response,
    configured_stayman_dual_major_response_policy_id,
    resolve_stayman_dual_major_response_policy,
)

__all__ += [
    "AbstentionCode", "ActionKind", "AnalysisAction", "AnalysisEvidence",
    "AnalysisStage", "AnalysisStatus", "DealAnalysisContext", "DealAnalysisResult",
    "Subsystem", "SubsystemResult", "analyze_deal_decision", "detect_analysis_stage",
    "DeclarerHandRole", "DeclarerPlayInput", "DeclarerPlayState",
    "DeclarerStateBuildResult", "DeclarerStateFailureCode", "PlayedCard", "Trick",
    "build_declarer_play_state", "legal_cards",
    "DeclarerRecommendation", "DeclarerRecommendationReason",
    "DeclarerRecommendationStatus", "DeclarerTechnique", "UNBLOCK_SOURCE",
    "evaluate_declarer_play",
    "KnownCardCountQuestion", "ProbabilityEvidence", "ProbabilityEvidenceFailureCode",
    "ProbabilityEvidenceResult", "ProbabilityEvidenceStatus", "ProbabilityEvidenceType",
    "collect_declarer_probability_evidence",
    "CalculationMode", "DEFAULT_PROBABILITY_ENGINE_REGISTRY", "FormulaIdentifier",
    "ProbabilityContext", "ProbabilityEngineFailureCode", "ProbabilityEngineRegistry",
    "ProbabilityEngineResult", "ProbabilityEngineStatus", "build_probability_context",
    "evaluate_probability", "MonteCarloQuestion", "ProbabilityQuestion",
    "RestrictedChoiceQuestion", "SuitDistributionQuestion", "TrumpBreakQuestion",
    "VacantPlacesQuestion",
    "DefensivePlayInput", "DefensivePlayState", "DefensiveStateBuildResult",
    "DefensiveStateFailureCode", "build_defensive_play_state",
    "build_defensive_probability_context",
    "OpeningLeadInput", "OpeningLeadState", "OpeningLeadStateBuildResult",
    "OpeningLeadStateFailureCode", "build_opening_lead_probability_context",
    "build_opening_lead_state",
    "OpeningLeadHonorStyle", "OpeningLeadLengthMethod", "OpeningLeadPolicy",
    "OpeningLeadPolicyAssessment", "OpeningLeadTopOfNothing",
    "assess_opening_lead_policy", "OPENING_LEAD_POLICY_OPTION",
    "DealSummaryFailureCode", "DealSummaryInput", "DealSummaryItem",
    "DealSummaryResult", "DealSummaryStatus", "build_deal_summary",
    "DealSummaryRenderedSection", "DealSummaryRendering",
    "DealSummaryRenderingStatus", "render_deal_summary",
    "DealSummaryPipelineFailureCode", "DealSummaryPipelineResult",
    "DealSummaryPipelineStatus", "build_and_render_deal_summary",
    "FullDealAnalysisInput", "FullDealAnalysisResult", "FullDealProbabilityRequest",
    "FullDealSkippedStage", "FullDealSkipReason", "analyze_full_deal",
]
