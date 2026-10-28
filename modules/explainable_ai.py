"""
Explainable AI (XAI) Module for Candidate Screening
Generates transparent match explanations, skill gap breakdowns,
evidence highlights, and factor attribution.
"""
from typing import Any, Dict, List

def generate_natural_language_explanation(
    candidate_name: str,
    score_data: Dict[str, Any],
    candidate_skills: List[str],
    jd_title: str = "Target Role"
) -> str:
    """
    Generate an executive summary explaining why the candidate received their score.
    """
    final_score = score_data.get("final_score", 0.0)
    tier = score_data.get("tier", "Match")
    skill_details = score_data.get("skill_details", {})
    evidence_details = score_data.get("evidence_details", {})
    components = score_data.get("components", {})

    matched_req = skill_details.get("matched_required", [])
    missing_req = skill_details.get("missing_required", [])
    matched_pref = skill_details.get("matched_preferred", [])

    total_req_count = len(matched_req) + len(missing_req)

    summary_lines = []

    # Opening verdict
    summary_lines.append(
        f"**{candidate_name}** achieved an overall Job-Fit Score of **{final_score}% ({tier})** for **{jd_title}**."
    )

    # Skill breakdown
    if total_req_count > 0:
        pct_matched = round((len(matched_req) / total_req_count) * 100)
        top_matched_str = ", ".join(matched_req[:4]) if matched_req else "None"
        summary_lines.append(
            f"• **Core Skills:** Matched {len(matched_req)} of {total_req_count} ({pct_matched}%) required skills ({top_matched_str})."
        )
    if missing_req:
        top_missing_str = ", ".join(missing_req[:3])
        summary_lines.append(
            f"• **Identified Skill Gaps:** Missing {len(missing_req)} required skill(s): `{top_missing_str}`."
        )
    else:
        summary_lines.append("• **Skill Coverage:** 100% of required skills are covered.")

    # Preferred skills
    if matched_pref:
        summary_lines.append(
            f"• **Bonus Competencies:** Covers preferred skills such as `{', '.join(matched_pref[:3])}`."
        )

    # Experience & Project Evidence
    cand_yrs = evidence_details.get("cand_years", 0)
    jd_yrs = evidence_details.get("jd_years", 0)
    if jd_yrs > 0:
        if cand_yrs >= jd_yrs:
            summary_lines.append(
                f"• **Experience Alignment:** Candidate has ~{cand_yrs:.1f} years, meeting or exceeding the required {jd_yrs:.1f} years."
            )
        else:
            summary_lines.append(
                f"• **Experience Consideration:** Has ~{cand_yrs:.1f} years compared to the requested {jd_yrs:.1f} years."
            )

    # Semantic contextual note
    sem_score = components.get("semantic_score", 0.0)
    if sem_score >= 70:
        summary_lines.append("• **Contextual Relevance:** Resume phrasing and project descriptions show high semantic alignment with job responsibilities.")
    elif sem_score < 45:
        summary_lines.append("• **Contextual Note:** Lower vocabulary and domain overlap with the job description duties.")

    return "\n\n".join(summary_lines)

def get_bonus_skills(candidate_skills: List[str], jd_skills: List[str]) -> List[str]:
    """Identify skills the candidate possesses that were not mentioned in the JD."""
    jd_lower = set(s.lower() for s in jd_skills)
    bonus = [s for s in candidate_skills if s.lower() not in jd_lower]
    return bonus

def prepare_radar_chart_data(score_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare normalized metrics for a radar or multi-bar visualization."""
    comp = score_data.get("components", {})
    ev = score_data.get("evidence_details", {})
    sk = score_data.get("skill_details", {})

    categories = [
        "Semantic Relevance",
        "Required Skills",
        "Preferred Skills",
        "Experience Match",
        "Project Alignment"
    ]

    values = [
        comp.get("semantic_score", 0.0),
        sk.get("req_coverage_pct", 0.0),
        sk.get("pref_coverage_pct") or 50.0,
        ev.get("exp_alignment_pct", 50.0),
        ev.get("evidence_relevance_pct", 50.0)
    ]

    return {
        "categories": categories,
        "values": [round(float(v), 1) for v in values]
    }
