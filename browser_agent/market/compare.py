from __future__ import annotations

from typing import Dict, List

from browser_agent.market.profiles import MARKET_PROFILES, OUR_PROFILE


CAPABILITY_WEIGHTS: Dict[str, Dict[str, int]] = {
    "comparison_recommendation": {
        "scenario_templates": 3,
        "verification_loop": 3,
        "audit_trail": 2,
        "human_handoff": 2,
    },
    "form_filling": {
        "scenario_templates": 2,
        "verification_loop": 3,
        "human_handoff": 3,
        "audit_trail": 2,
    },
    "booking_reservation": {
        "scenario_templates": 2,
        "verification_loop": 3,
        "human_handoff": 4,
        "audit_trail": 3,
    },
    "lead_collection": {
        "scenario_templates": 3,
        "verification_loop": 2,
        "audit_trail": 3,
        "persistent_session": 2,
    },
    "monitoring_alerts": {
        "scenario_templates": 3,
        "verification_loop": 2,
        "audit_trail": 3,
        "market_benchmarking": 2,
    },
    "qa_regression": {
        "scenario_templates": 3,
        "verification_loop": 4,
        "audit_trail": 3,
        "deterministic_tests": 4,
    },
    "research": {
        "scenario_templates": 2,
        "verification_loop": 2,
        "audit_trail": 2,
        "market_benchmarking": 2,
    },
}


def _score(capabilities: Dict[str, bool], weights: Dict[str, int]) -> int:
    score = 0
    for capability, weight in weights.items():
        if capabilities.get(capability, False):
            score += weight
    return score


def compare_market_profiles(scenario: str) -> Dict[str, object]:
    weights = CAPABILITY_WEIGHTS.get(scenario, CAPABILITY_WEIGHTS["research"])
    profiles = [OUR_PROFILE, *MARKET_PROFILES]
    scored: List[Dict[str, object]] = []

    for profile in profiles:
        score = _score(profile.capabilities, weights)
        missing = [cap for cap, enabled in weights.items() if enabled and not profile.capabilities.get(cap, False)]
        scored.append(
            {
                "name": profile.name,
                "category": profile.category,
                "score": score,
                "source_url": profile.source_url,
                "updated_on": profile.updated_on,
                "strengths": profile.strengths,
                "limits": profile.limits,
                "missing_weighted_capabilities": missing,
            }
        )

    scored.sort(key=lambda item: int(item["score"]), reverse=True)
    our_capabilities = OUR_PROFILE.capabilities
    surpass_points = []
    for capability in weights:
        if not our_capabilities.get(capability, False):
            continue
        lacking = sum(
            1 for profile in MARKET_PROFILES if not profile.capabilities.get(capability, False)
        )
        if lacking >= 3:
            surpass_points.append(capability)

    best_external = next(item for item in scored if item["name"] != OUR_PROFILE.name)
    return {
        "scenario": scenario,
        "weights": weights,
        "leader": scored[0]["name"],
        "best_external": best_external["name"],
        "our_advantage_capabilities": surpass_points,
        "profiles": scored,
    }
