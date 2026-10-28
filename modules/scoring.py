"""
Multimodal Candidate Scoring Engine
Implements the blueprint formula:
S = w_s * S_semantic + w_k * S_skills + w_e * S_evidence
Where:
- S_semantic: contextual similarity between JD and candidate content
- S_skills: coverage of required and preferred skills
- S_evidence: evidence of relevant experience and project alignment
"""
from typing import Any, Dict, List, Tuple
import numpy as np

def calculate_skills_score(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str]
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute skill coverage score:
    S_skills = 0.8 * req_coverage + 0.2 * pref_coverage
    """
    cand_set = set(s.lower() for s in candidate_skills)
    req_set = set(s.lower() for s in required_skills)
    pref_set = set(s.lower() for s in preferred_skills)

    matched_req = [s for s in required_skills if s.lower() in cand_set]
    missing_req = [s for s in required_skills if s.lower() not in cand_set]

    matched_pref = [s for s in preferred_skills if s.lower() in cand_set]
    missing_pref = [s for s in preferred_skills if s.lower() not in cand_set]

    req_coverage = len(matched_req) / len(req_set) if req_set else 1.0
    pref_coverage = len(matched_pref) / len(pref_set) if pref_set else 1.0

    if req_set and pref_set:
        skill_score = 0.80 * req_coverage + 0.20 * pref_coverage
    elif req_set:
        skill_score = req_coverage
    elif pref_set:
        skill_score = pref_coverage
    else:
        skill_score = 1.0

    details = {
        "score": float(np.clip(skill_score, 0.0, 1.0)),
        "matched_required": matched_req,
        "missing_required": missing_req,
        "matched_preferred": matched_pref,
        "missing_preferred": missing_pref,
        "req_coverage_pct": round(req_coverage * 100, 1),
        "pref_coverage_pct": round(pref_coverage * 100, 1) if pref_set else None
    }
    return details["score"], details

def calculate_evidence_score(
    candidate_profile: Dict[str, Any],
    jd_profile: Dict[str, Any],
    evidence_matches: List[Dict[str, Any]]
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute evidence score based on:
    1. Experience duration alignment (candidate years vs JD required years)
    2. Deep project/experience relevance matches
    """
    cand_exp = candidate_profile.get("experience_years", 1.0)
    jd_exp = jd_profile.get("min_experience_years", 2.0)

    # Ratio of experience
    if jd_exp > 0:
        exp_ratio = min(cand_exp / jd_exp, 1.25) / 1.25
    else:
        exp_ratio = 1.0

    # Project / section relevance
    sections = candidate_profile.get("sections", {})
    has_projects = bool(sections.get("projects"))
    has_experience = bool(sections.get("experience"))

    project_depth_bonus = 0.0
    if has_projects and has_experience:
        project_depth_bonus = 0.15
    elif has_projects or has_experience:
        project_depth_bonus = 0.08

    # Semantic evidence alignment average
    if evidence_matches:
        top_sims = [m["best_similarity"] / 100.0 for m in evidence_matches]
        avg_evidence_sim = float(np.mean(top_sims))
    else:
        avg_evidence_sim = 0.50

    # Combined Evidence Score
    evidence_score = 0.45 * exp_ratio + 0.40 * avg_evidence_sim + 0.15 * project_depth_bonus
    evidence_score = float(np.clip(evidence_score, 0.0, 1.0))

    details = {
        "score": evidence_score,
        "cand_years": cand_exp,
        "jd_years": jd_exp,
        "exp_alignment_pct": round(exp_ratio * 100, 1),
        "evidence_relevance_pct": round(avg_evidence_sim * 100, 1),
        "has_projects": has_projects,
        "has_experience": has_experience
    }
    return evidence_score, details

def calculate_candidate_score(
    candidate_profile: Dict[str, Any],
    jd_profile: Dict[str, Any],
    semantic_similarity: float,
    evidence_matches: List[Dict[str, Any]],
    weight_semantic: float = 0.40,
    weight_skills: float = 0.40,
    weight_evidence: float = 0.20
) -> Dict[str, Any]:
    """
    Calculate full multi-signal job-fit score and return comprehensive breakdown.
    Formula: S = w_s * S_semantic + w_k * S_skills + w_e * S_evidence
    """
    # Normalize weights to sum to 1.0
    total_w = weight_semantic + weight_skills + weight_evidence
    if total_w <= 0:
        w_s, w_k, w_e = 0.40, 0.40, 0.20
    else:
        w_s = weight_semantic / total_w
        w_k = weight_skills / total_w
        w_e = weight_evidence / total_w

    s_skills, skill_details = calculate_skills_score(
        candidate_profile.get("skills", []),
        jd_profile.get("required_skills", []),
        jd_profile.get("preferred_skills", [])
    )

    s_evidence, evidence_details = calculate_evidence_score(
        candidate_profile,
        jd_profile,
        evidence_matches
    )

    s_semantic = float(np.clip(semantic_similarity, 0.0, 1.0))

    # Overall Job-Fit Score (0.0 to 100.0)
    final_score = (w_s * s_semantic + w_k * s_skills + w_e * s_evidence) * 100.0
    final_score = round(float(np.clip(final_score, 0.0, 100.0)), 1)

    # Classify fit tier
    if final_score >= 80.0:
        tier = "Strong Match"
        tier_color = "#10b981"  # Emerald
    elif final_score >= 65.0:
        tier = "Good Match"
        tier_color = "#3b82f6"  # Blue
    elif final_score >= 50.0:
        tier = "Moderate Match"
        tier_color = "#f59e0b"  # Amber
    else:
        tier = "Low Match"
        tier_color = "#ef4444"  # Red

    return {
        "final_score": final_score,
        "tier": tier,
        "tier_color": tier_color,
        "weights": {
            "semantic": round(w_s, 2),
            "skills": round(w_k, 2),
            "evidence": round(w_e, 2)
        },
        "components": {
            "semantic_score": round(s_semantic * 100, 1),
            "skills_score": round(s_skills * 100, 1),
            "evidence_score": round(s_evidence * 100, 1)
        },
        "skill_details": skill_details,
        "evidence_details": evidence_details
    }
