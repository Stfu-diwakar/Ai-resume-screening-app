"""
HireSense AI - Semantic Resume Screening & Career Recommendation Engine
Main Streamlit Application
"""
import io
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from modules.academic_eval import run_academic_benchmark
from modules.database import get_recent_runs, get_run_results, save_job, save_screening_run
from modules.explainable_ai import (
    generate_natural_language_explanation,
    get_bonus_skills,
    prepare_radar_chart_data,
)
from modules.parser import parse_job_description, parse_resume
from modules.recommender import generate_recommendations
from modules.scoring import calculate_candidate_score
from modules.semantic_matcher import SemanticMatcher, TfidfBaseline

# Page Configuration
st.set_page_config(
    page_title="HireSense AI | Semantic Resume Screening",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_file = Path("assets/style.css")
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1>HireSense AI</h1>
            <p>Semantic Resume Screening, Explainable Candidate Ranking & Career Recommendation Engine</p>
        </div>
        <div style="text-align: right; background: rgba(255,255,255,0.12); padding: 0.6rem 1.2rem; border-radius: 10px; margin-top: 0.5rem;">
            <span style="font-size: 0.85rem; color: #cbd5e1;">NLP Model:</span><br/>
            <strong style="color: #ffffff; font-size: 1.05rem;">Sentence-BERT (all-MiniLM-L6-v2)</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize Session State
if "screening_results" not in st.session_state:
    st.session_state.screening_results = None
if "parsed_job" not in st.session_state:
    st.session_state.parsed_job = None
if "selected_candidate_idx" not in st.session_state:
    st.session_state.selected_candidate_idx = 0
if "benchmark_data" not in st.session_state:
    st.session_state.benchmark_data = None

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Scoring Model Tuning")
    st.caption("Configurable formula:")
    st.latex(r"S = w_s S_{\text{semantic}} + w_k S_{\text{skills}} + w_e S_{\text{evidence}}")

    preset = st.selectbox(
        "Weight Preset",
        ["Balanced (Recommended)", "Skill Heavy", "Experience Heavy", "Custom"]
    )

    if preset == "Balanced (Recommended)":
        default_ws, default_wk, default_we = 40, 40, 20
    elif preset == "Skill Heavy":
        default_ws, default_wk, default_we = 25, 55, 20
    elif preset == "Experience Heavy":
        default_ws, default_wk, default_we = 30, 30, 40
    else:
        default_ws, default_wk, default_we = 40, 40, 20

    w_semantic = st.slider("Contextual Semantic Weight (w_s)", 0, 100, default_ws, 5)
    w_skills = st.slider("Skill Match Weight (w_k)", 0, 100, default_wk, 5)
    w_evidence = st.slider("Project & Experience Weight (w_e)", 0, 100, default_we, 5)

    tot_weight = w_semantic + w_skills + w_evidence
    if tot_weight > 0:
        st.caption(f"Normalized Weights: **{w_semantic/tot_weight:.2f}** | **{w_skills/tot_weight:.2f}** | **{w_evidence/tot_weight:.2f}**")
    else:
        st.error("Total weight cannot be zero.")

    st.markdown("---")
    st.markdown("### 🧠 Semantic Model Engine")
    model_choice = st.selectbox("Embedding Architecture", ["all-MiniLM-L6-v2 (Fast & Accurate)", "paraphrase-MiniLM-L3-v2"])
    st.info("💡 **Explainable AI Mode Enabled**: System assists human recruiters with granular reasoning rather than automated rejection.")

# Main Navigation Tabs
tab_screen, tab_explain, tab_career, tab_academic, tab_history = st.tabs([
    "🎯 Screening Dashboard",
    "🔍 Explainable AI & Inspector",
    "🚀 Career Recommendations",
    "📊 Academic Benchmark (S-BERT vs TF-IDF)",
    "📜 Screening History & Database"
])

# ==============================================================================
# TAB 1: SCREENING DASHBOARD
# ==============================================================================
with tab_screen:
    col_jd, col_res = st.columns([1, 1], gap="large")

    with col_jd:
        st.markdown("### 1. Job Description")
        sample_jobs = list(config.SAMPLE_JOBS_DIR.glob("*.txt"))
        job_options = ["Custom Input"] + [j.stem.replace("job_", "").replace("_", " ").title() for j in sample_jobs]
        selected_job_preset = st.selectbox("Load Sample Job or Enter Custom:", job_options)

        default_jd_text = ""
        if selected_job_preset != "Custom Input":
            matched_file = next(j for j in sample_jobs if j.stem.replace("job_", "").replace("_", " ").title() == selected_job_preset)
            default_jd_text = matched_file.read_text(encoding="utf-8")

        jd_text_input = st.text_area(
            "Job Description Text",
            value=default_jd_text,
            height=260,
            placeholder="Paste your job description requirements here..."
        )

        jd_title_input = st.text_input("Role Title", value="Senior Machine Learning Engineer" if "Senior Machine" in jd_text_input else "Target Role")

    with col_res:
        st.markdown("### 2. Candidate Resumes")
        uploaded_files = st.file_uploader(
            "Upload Candidate Resumes (PDF, DOCX, or TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )

        load_sample_btn = st.button("📁 Load All 5 Pre-Built Sample Resumes (PDF / DOCX)", use_container_width=True)

        st.caption("Includes: Senior ML Engineer, Full-Stack Dev, Data Scientist, DevOps Engineer, and Junior Intern.")

    # Action Trigger
    st.markdown("---")
    run_screening_btn = st.button("⚡ Run HireSense Screening & Candidate Ranking", type="primary", use_container_width=True)

    # Process Resumes
    if run_screening_btn or (load_sample_btn and jd_text_input.strip()):
        if not jd_text_input.strip():
            st.error("Please provide or select a Job Description first.")
        else:
            with st.spinner("Analyzing job description and parsing resumes with Sentence-BERT & spaCy..."):
                # 1. Parse Job
                parsed_jd = parse_job_description(jd_text_input, title=jd_title_input)
                st.session_state.parsed_job = parsed_jd
                job_id = save_job(parsed_jd)

                # 2. Collect Candidate Files
                files_to_process = []
                if uploaded_files:
                    for f in uploaded_files:
                        files_to_process.append((f.name, f.read()))
                elif load_sample_btn or not uploaded_files:
                    # Use sample resumes
                    sample_dir = config.SAMPLE_RESUMES_DIR
                    for s_file in list(sample_dir.glob("*.pdf")) + list(sample_dir.glob("*.docx")):
                        files_to_process.append((s_file.name, s_file.read_bytes()))

                if not files_to_process:
                    st.warning("No resumes found. Please upload resumes or click 'Load Sample Resumes'.")
                else:
                    # 3. Parse and Match Candidates
                    matcher = SemanticMatcher()
                    scored_candidates = []

                    # Extract key sentences from JD for evidence matching
                    jd_sentences = [
                        s.strip() for s in parsed_jd["full_text"].splitlines()
                        if len(s.strip()) > 30 and not s.strip().startswith("Job Title")
                    ][:6]

                    for fname, fbytes in files_to_process:
                        cand_profile = parse_resume(fbytes, fname)

                        # Contextual semantic similarity
                        sem_sim = matcher.calculate_similarity(parsed_jd["full_text"], cand_profile["full_text"])

                        # Find matching evidence snippets
                        evidence_matches = matcher.find_top_evidence(jd_sentences, cand_profile["full_text"])

                        # Compute weighted multimodal score
                        score_data = calculate_candidate_score(
                            candidate_profile=cand_profile,
                            jd_profile=parsed_jd,
                            semantic_similarity=sem_sim,
                            evidence_matches=evidence_matches,
                            weight_semantic=w_semantic,
                            weight_skills=w_skills,
                            weight_evidence=w_evidence
                        )

                        # Generate explanation
                        explanation = generate_natural_language_explanation(
                            candidate_name=cand_profile["candidate_name"],
                            score_data=score_data,
                            candidate_skills=cand_profile["skills"],
                            jd_title=parsed_jd["title"]
                        )

                        scored_candidates.append({
                            **cand_profile,
                            "semantic_similarity": sem_sim,
                            "score_data": score_data,
                            "evidence_matches": evidence_matches,
                            "explanation": explanation
                        })

                    # Sort candidates by final score descending
                    scored_candidates.sort(key=lambda x: x["score_data"]["final_score"], reverse=True)
                    st.session_state.screening_results = scored_candidates

                    # Save run into SQLite database
                    save_screening_run(
                        job_title=parsed_jd["title"],
                        job_id=job_id,
                        weights={"semantic": w_semantic, "skills": w_skills, "evidence": w_evidence},
                        ranked_candidates=scored_candidates
                    )

    # Display Screening Results
    if st.session_state.screening_results and st.session_state.parsed_job:
        candidates = st.session_state.screening_results
        parsed_jd = st.session_state.parsed_job

        st.markdown("### 🏆 Screening Results & Candidate Rankings")

        # Top KPI Metrics
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        top_cand = candidates[0]
        avg_score = sum(c["score_data"]["final_score"] for c in candidates) / len(candidates)
        strong_matches_count = sum(1 for c in candidates if c["score_data"]["tier"] == "Strong Match")

        with kpi1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Candidates Screened</div>
                <div class="metric-value">{len(candidates)}</div>
                <div class="metric-subtitle">Across PDF & DOCX resumes</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Top Ranked Fit</div>
                <div class="metric-value" style="color: {top_cand['score_data']['tier_color']};">{top_cand['score_data']['final_score']}%</div>
                <div class="metric-subtitle">{top_cand['candidate_name']} ({top_cand['score_data']['tier']})</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Average Fit Score</div>
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-subtitle">Cohort Benchmark</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Strong Matches</div>
                <div class="metric-value" style="color: #10b981;">{strong_matches_count}</div>
                <div class="metric-subtitle">Score ≥ 80.0%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Leaderboard Chart & Component Stack
        chart_col1, chart_col2 = st.columns([1.2, 1])

        with chart_col1:
            df_ranks = pd.DataFrame([
                {
                    "Candidate": c["candidate_name"],
                    "Fit Score (%)": c["score_data"]["final_score"],
                    "Tier": c["score_data"]["tier"],
                    "Color": c["score_data"]["tier_color"]
                } for c in candidates
            ])
            fig_bar = px.bar(
                df_ranks,
                x="Fit Score (%)",
                y="Candidate",
                orientation="h",
                color="Tier",
                color_discrete_map={
                    "Strong Match": "#10b981",
                    "Good Match": "#3b82f6",
                    "Moderate Match": "#f59e0b",
                    "Low Match": "#ef4444"
                },
                text="Fit Score (%)",
                title="Candidate Fit Ranking (Multimodal Weighted Score)"
            )
            fig_bar.update_layout(yaxis=dict(autorange="reversed"), height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)

        with chart_col2:
            # Component breakdown chart
            breakdown_data = []
            for c in candidates:
                comp = c["score_data"]["components"]
                breakdown_data.append({"Candidate": c["candidate_name"], "Signal": "Semantic Context", "Score": comp["semantic_score"]})
                breakdown_data.append({"Candidate": c["candidate_name"], "Signal": "Skill Coverage", "Score": comp["skills_score"]})
                breakdown_data.append({"Candidate": c["candidate_name"], "Signal": "Project/Experience", "Score": comp["evidence_score"]})
            df_comp = pd.DataFrame(breakdown_data)

            fig_comp = px.bar(
                df_comp,
                x="Candidate",
                y="Score",
                color="Signal",
                barmode="group",
                title="Score Factor Signals Comparison",
                color_discrete_sequence=["#6366f1", "#10b981", "#f59e0b"]
            )
            fig_comp.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), yaxis_title="Score (0-100)")
            st.plotly_chart(fig_comp, use_container_width=True)

        # Candidate Ranking Table
        st.markdown("#### Candidate Cohort Leaderboard")
        table_rows = []
        for rank, c in enumerate(candidates, 1):
            sc = c["score_data"]
            sk = sc["skill_details"]
            table_rows.append({
                "Rank": f"#{rank}",
                "Candidate Name": c["candidate_name"],
                "Job-Fit Score": f"{sc['final_score']}%",
                "Fit Tier": sc["tier"],
                "Experience": f"~{c['experience_years']:.1f} yrs",
                "Required Skills Matched": f"{len(sk['matched_required'])} / {len(sk['matched_required']) + len(sk['missing_required'])}",
                "Contact Email": c["email"] or "N/A",
                "File Source": c["filename"]
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

        # Quick CSV Download
        csv_buffer = io.StringIO()
        pd.DataFrame(table_rows).to_csv(csv_buffer, index=False)
        st.download_button(
            "📥 Download Candidate Ranking Report (CSV)",
            data=csv_buffer.getvalue(),
            file_name="hiresense_candidate_rankings.csv",
            mime="text/csv"
        )

# ==============================================================================
# TAB 2: EXPLAINABLE AI & INSPECTOR
# ==============================================================================
with tab_explain:
    st.markdown("### 🔍 Transparent Decision Inspector")
    st.caption("Unpacking the factors, skill coverage, and project evidence behind each candidate's score.")

    if not st.session_state.screening_results:
        st.info("Please run the screening on the first tab to inspect candidate explanations.")
    else:
        candidates = st.session_state.screening_results
        candidate_names = [f"#{i+1} {c['candidate_name']} ({c['score_data']['final_score']}%)" for i, c in enumerate(candidates)]

        selected_cand_idx = st.selectbox(
            "Select Candidate to Inspect:",
            range(len(candidates)),
            format_func=lambda i: candidate_names[i]
        )
        cand = candidates[selected_cand_idx]
        score_data = cand["score_data"]
        skill_details = score_data["skill_details"]
        evidence_details = score_data["evidence_details"]
        components = score_data["components"]

        # Profile Summary Header
        pcol1, pcol2 = st.columns([1.5, 1])
        with pcol1:
            st.markdown(f"## {cand['candidate_name']}")
            contact_str = f"📧 `{cand['email'] or 'N/A'}` | 📞 `{cand['phone'] or 'N/A'}` | 📄 `{cand['filename']}`"
            st.markdown(contact_str)
            if cand.get("linkedin"):
                st.markdown(f"[LinkedIn Profile]({cand['linkedin']}) | [GitHub Profile]({cand.get('github', '#')})")

            st.markdown("#### Executive Match Explanation")
            st.info(cand["explanation"])

        with pcol2:
            st.markdown(f"""
            <div style="text-align: center; background: #f8fafc; border: 2px solid {score_data['tier_color']}; border-radius: 16px; padding: 2rem 1.5rem; margin-top: 1rem;">
                <div style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; font-weight: 700;">Job-Fit Score</div>
                <div style="font-size: 3.5rem; font-weight: 900; color: {score_data['tier_color']}; line-height: 1.1;">{score_data['final_score']}%</div>
                <div style="display: inline-block; background: {score_data['tier_color']}; color: white; padding: 0.3rem 1rem; border-radius: 20px; font-weight: 700; margin-top: 0.75rem; font-size: 0.95rem;">
                    {score_data['tier']}
                </div>
                <div style="margin-top: 1.25rem; font-size: 0.85rem; color: #64748b; text-align: left;">
                    <div>• <b>Contextual Semantic:</b> {components['semantic_score']}%</div>
                    <div>• <b>Skill Coverage:</b> {components['skills_score']}%</div>
                    <div>• <b>Experience Alignment:</b> {components['evidence_score']}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Radar / Factor Visualization
        r_col1, r_col2 = st.columns([1, 1])

        with r_col1:
            st.markdown("#### Multimodal Competency Radar")
            radar_data = prepare_radar_chart_data(score_data)
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_data["values"] + [radar_data["values"][0]],
                theta=radar_data["categories"] + [radar_data["categories"][0]],
                fill='toself',
                fillcolor='rgba(99, 102, 241, 0.25)',
                line=dict(color='#4f46e5', width=2),
                name=cand["candidate_name"]
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100])
                ),
                showlegend=False,
                height=380,
                margin=dict(l=40, r=40, t=30, b=30)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with r_col2:
            st.markdown("#### Skill Categorization Breakdown")

            st.markdown("**Matched Required Skills (Passed):**")
            if skill_details["matched_required"]:
                badges = "".join([f'<span class="skill-badge badge-matched">✓ {s}</span>' for s in skill_details["matched_required"]])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.caption("None matched.")

            st.markdown("<br/>**Missing Required Skills (Gaps):**", unsafe_allow_html=True)
            if skill_details["missing_required"]:
                badges = "".join([f'<span class="skill-badge badge-missing-req">✕ {s}</span>' for s in skill_details["missing_required"]])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.markdown('<span class="skill-badge badge-matched">✓ No Required Skill Gaps!</span>', unsafe_allow_html=True)

            if skill_details.get("matched_preferred"):
                st.markdown("<br/>**Matched Preferred / Bonus Skills:**", unsafe_allow_html=True)
                badges = "".join([f'<span class="skill-badge badge-bonus">★ {s}</span>' for s in skill_details["matched_preferred"]])
                st.markdown(badges, unsafe_allow_html=True)

            # Additional Candidate Skills
            bonus_skills = get_bonus_skills(cand["skills"], st.session_state.parsed_job["skills"])
            if bonus_skills:
                st.markdown("<br/>**Other Demonstrated Skills in Resume:**", unsafe_allow_html=True)
                badges = "".join([f'<span class="skill-badge badge-bonus">{s}</span>' for s in bonus_skills[:10]])
                st.markdown(badges, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 📑 Extracted Project & Experience Evidence")
        st.caption("Specific resume bullet points contextually matched with job requirements using Sentence-BERT embeddings:")

        evidence_list = cand.get("evidence_matches", [])
        if evidence_list:
            for item in evidence_list:
                with st.expander(f"📌 Requirement: **{item['requirement'][:80]}...** (Top Match: {item['best_similarity']}%)"):
                    st.markdown(f"**Target Requirement:** `{item['requirement']}`")
                    st.markdown("**Matching Resume Excerpts:**")
                    for m in item["top_matches"]:
                        st.markdown(f"""
                        <div class="evidence-quote">
                            "{m['text']}"
                            <div style="font-size: 0.78rem; color: #2563eb; font-weight: 600; margin-top: 0.3rem;">
                                Semantic Relevance Score: {m['similarity']}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No direct sentence-level matches found.")

# ==============================================================================
# TAB 3: CAREER RECOMMENDATIONS
# ==============================================================================
with tab_career:
    st.markdown("### 🚀 Career Recommendation Engine")
    st.caption("Personalized learning pathways, curated resources, and portfolio project blueprints based on identified skill gaps.")

    if not st.session_state.screening_results:
        st.info("Please screen resumes on the first tab to generate tailored candidate career recommendations.")
    else:
        candidates = st.session_state.screening_results
        cand_names = [f"{c['candidate_name']} ({c['score_data']['tier']})" for c in candidates]
        rec_cand_idx = st.selectbox("Select Candidate for Targeted Upskilling Plan:", range(len(candidates)), format_func=lambda i: cand_names[i])
        sel_cand = candidates[rec_cand_idx]

        sk_details = sel_cand["score_data"]["skill_details"]
        missing_req = sk_details.get("missing_required", [])
        missing_pref = sk_details.get("missing_preferred", [])

        # Generate recommendations
        recs = generate_recommendations(
            missing_required_skills=missing_req,
            missing_preferred_skills=missing_pref,
            target_role=st.session_state.parsed_job["title"]
        )

        st.markdown(f"#### Upskilling Roadmap for **{sel_cand['candidate_name']}**")
        st.markdown(f"**Target Role:** `{recs['target_role']}` | **Identified Gaps:** `{recs['total_gaps_count']} skill(s)`")

        # 3-Phase Roadmap Timeline
        st.markdown("#### 🗺️ Strategic 3-Phase Upskilling Roadmap")
        road_cols = st.columns(3)
        for i, stage in enumerate(recs["learning_roadmap_stages"]):
            with road_cols[i]:
                st.markdown(f"""
                <div class="rec-box" style="border-left-color: {'#ef4444' if i==0 else '#6366f1' if i==1 else '#10b981'}; min-height: 160px;">
                    <div class="rec-title">{stage['stage']}</div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: #4338ca; margin-bottom: 0.4rem;">
                        Focus: {', '.join(stage['focus'])}
                    </div>
                    <div class="rec-desc">{stage['goal']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        col_gaps, col_proj = st.columns([1.1, 1], gap="large")

        with col_gaps:
            st.markdown("#### 📚 Priority Learning Pathways & Curated Resources")
            if recs["priority_1_gaps"]:
                st.markdown("##### Priority 1: Mandatory Role Gaps")
                for item in recs["priority_1_gaps"]:
                    with st.expander(f"🚨 **{item['skill']}** ({item['estimated_time']} | {item['level']})"):
                        st.markdown(f"**Proficiency Level Target:** {item['level']}")
                        st.markdown(f"**Estimated Time Commitment:** {item['estimated_time']}")
                        st.markdown("**Recommended Courses & Tutorials:**")
                        for r in item["resources"]:
                            st.markdown(f"• [{r['title']}]({r['url']}) `({r['type']})`")
            else:
                st.success("🎉 No Priority 1 skill gaps! Candidate meets all required skills.")

            if recs["priority_2_gaps"]:
                st.markdown("##### Priority 2: Competitive Edge Skills")
                for item in recs["priority_2_gaps"]:
                    with st.expander(f"⭐ **{item['skill']}** ({item['estimated_time']})"):
                        for r in item["resources"]:
                            st.markdown(f"• [{r['title']}]({r['url']}) `({r['type']})`")

        with col_proj:
            st.markdown("#### 🛠️ Recommended Portfolio Projects")
            st.caption("Hands-on proof-of-work project blueprints to prove competence on resume & GitHub:")
            for proj in recs["recommended_projects"]:
                st.markdown(f"""
                <div class="rec-box">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="rec-title">{proj['title']}</span>
                        <span style="font-size: 0.75rem; background: #e0e7ff; color: #3730a3; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 700;">
                            {proj.get('urgency', 'Portfolio')}
                        </span>
                    </div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #0284c7; margin-bottom: 0.4rem;">
                        Target Competency: {proj.get('target_skill', 'System Architecture')}
                    </div>
                    <div class="rec-desc">{proj['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

# ==============================================================================
# TAB 4: ACADEMIC BENCHMARK (S-BERT vs TF-IDF)
# ==============================================================================
with tab_academic:
    st.markdown("### 📊 Academic Benchmark: Sentence-BERT vs TF-IDF Baseline")
    st.caption("Rigorous comparative evaluation addressing the blueprint's academic requirement: embedding contextual representation vs classic lexical n-gram matching.")

    run_eval_btn = st.button("🚀 Run Comparative Benchmark on Ground-Truth Dataset", type="primary")

    if run_eval_btn or st.session_state.benchmark_data is not None:
        if st.session_state.benchmark_data is None:
            with st.spinner("Computing Information Retrieval metrics, Spearman rank correlations, and synonym tests..."):
                st.session_state.benchmark_data = run_academic_benchmark()

        bench = st.session_state.benchmark_data
        metrics = bench["metrics_summary"]

        # Comparative Metrics Cards
        st.markdown("#### 1. Information Retrieval & Ranking Metrics")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)

        with m_col1:
            st.metric(
                label="NDCG@3 (Ranking Quality)",
                value=f"{metrics['S-BERT']['NDCG@3']}",
                delta=f"+{metrics['S-BERT']['NDCG@3'] - metrics['TF-IDF']['NDCG@3']:.3f} vs TF-IDF"
            )
        with m_col2:
            st.metric(
                label="Precision@1 (Top 1 Accuracy)",
                value=f"{metrics['S-BERT']['P@1']:.1%}",
                delta=f"+{(metrics['S-BERT']['P@1'] - metrics['TF-IDF']['P@1'])*100:.1f}% vs TF-IDF"
            )
        with m_col3:
            st.metric(
                label="Spearman Rank Correlation (ρ)",
                value=f"{metrics['S-BERT']['Spearman_rho']:.3f}",
                delta=f"+{metrics['S-BERT']['Spearman_rho'] - metrics['TF-IDF']['Spearman_rho']:.3f} vs TF-IDF"
            )
        with m_col4:
            st.metric(
                label="Latency per Resume",
                value=f"{metrics['S-BERT']['Latency_ms']:.1f} ms",
                delta=f"-{metrics['S-BERT']['Latency_ms'] - metrics['TF-IDF']['Latency_ms']:.1f} ms vs TF-IDF",
                delta_color="inverse"
            )

        st.markdown("<br/>", unsafe_allow_html=True)

        # Metrics Comparison Table
        df_metrics = pd.DataFrame([
            {
                "Evaluation Metric": "Normalized Discounted Cumulative Gain (NDCG@3)",
                "Sentence-BERT (all-MiniLM-L6-v2)": metrics["S-BERT"]["NDCG@3"],
                "TF-IDF Baseline": metrics["TF-IDF"]["NDCG@3"],
                "Improvement": f"+{(metrics['S-BERT']['NDCG@3'] - metrics['TF-IDF']['NDCG@3']):.3f}"
            },
            {
                "Evaluation Metric": "Precision@1 (Top Recommended Candidate)",
                "Sentence-BERT (all-MiniLM-L6-v2)": f"{metrics['S-BERT']['P@1']:.2f}",
                "TF-IDF Baseline": f"{metrics['TF-IDF']['P@1']:.2f}",
                "Improvement": f"+{(metrics['S-BERT']['P@1'] - metrics['TF-IDF']['P@1']):.2f}"
            },
            {
                "Evaluation Metric": "Precision@3 (Top 3 Candidates Relevance)",
                "Sentence-BERT (all-MiniLM-L6-v2)": f"{metrics['S-BERT']['P@3']:.2f}",
                "TF-IDF Baseline": f"{metrics['TF-IDF']['P@3']:.2f}",
                "Improvement": f"+{(metrics['S-BERT']['P@3'] - metrics['TF-IDF']['P@3']):.2f}"
            },
            {
                "Evaluation Metric": "Mean Reciprocal Rank (MRR)",
                "Sentence-BERT (all-MiniLM-L6-v2)": f"{metrics['S-BERT']['MRR']:.2f}",
                "TF-IDF Baseline": f"{metrics['TF-IDF']['MRR']:.2f}",
                "Improvement": f"+{(metrics['S-BERT']['MRR'] - metrics['TF-IDF']['MRR']):.2f}"
            },
            {
                "Evaluation Metric": "Spearman Rank Correlation (ρ)",
                "Sentence-BERT (all-MiniLM-L6-v2)": f"{metrics['S-BERT']['Spearman_rho']:.3f}",
                "TF-IDF Baseline": f"{metrics['TF-IDF']['Spearman_rho']:.3f}",
                "Improvement": f"+{(metrics['S-BERT']['Spearman_rho'] - metrics['TF-IDF']['Spearman_rho']):.3f}"
            },
            {
                "Evaluation Metric": "Inference Latency (ms)",
                "Sentence-BERT (all-MiniLM-L6-v2)": f"{metrics['S-BERT']['Latency_ms']} ms",
                "TF-IDF Baseline": f"{metrics['TF-IDF']['Latency_ms']} ms",
                "Improvement": "TF-IDF faster (lexical lookup)"
            }
        ])
        st.dataframe(df_metrics, use_container_width=True)

        st.markdown("---")

        # Lexical Gap / Synonym Robustness Test
        st.markdown("#### 2. Lexical Mismatch & Synonym Understanding Test")
        st.markdown(
            "This experiment demonstrates the critical flaw in keyword/TF-IDF models: when candidates and job descriptions use different wording for the same technical concept, TF-IDF drops to near zero, whereas Sentence-BERT captures the underlying semantic meaning."
        )

        df_synonyms = pd.DataFrame(bench["synonym_tests"])
        st.dataframe(df_synonyms[[
            "concept", "query", "doc", "sbert_score", "tfidf_score", "advantage"
        ]].rename(columns={
            "concept": "Concept Tested",
            "query": "Job Description Phrasing",
            "doc": "Resume Phrasing",
            "sbert_score": "S-BERT Sim (%)",
            "tfidf_score": "TF-IDF Sim (%)",
            "advantage": "S-BERT Lead (+%)"
        }), use_container_width=True)

        # Plotly Comparison Bar Chart for Synonym Tests
        fig_syn = px.bar(
            df_synonyms,
            x="concept",
            y=["sbert_score", "tfidf_score"],
            barmode="group",
            title="Semantic Understanding vs Lexical Keyword Matching",
            labels={"value": "Similarity Score (%)", "concept": "Technical Concept", "variable": "Model"},
            color_discrete_map={"sbert_score": "#6366f1", "tfidf_score": "#94a3b8"}
        )
        fig_syn.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_syn, use_container_width=True)

        # Academic Methodology Note
        with st.expander("📖 Academic Methodology & Theoretical Discussion"):
            st.markdown("""
            ### Why Sentence-BERT Outperforms TF-IDF in Resume Screening
            1. **Dense Vector Representations vs Sparse Bag-of-Words:**
               - TF-IDF relies entirely on exact string overlap and token frequency. It cannot generalize to acronyms (e.g., `K8s` vs `Kubernetes`), aliases (`Golang` vs `Go`), or related paradigms (`Deep Neural Networks` vs `Transformers`).
               - Sentence-BERT uses Siamese transformer networks with mean pooling fine-tuned on NLI and STS datasets, projecting semantically similar sentences into adjacent positions in a 384-dimensional embedding manifold.
            2. **Sub-word Tokenization:**
               - Sentence-BERT's WordPiece tokenizer handles compound engineering names and out-of-vocabulary variations gracefully, preventing the vocabulary mismatch problem common in standard recruitment ATS systems.
            3. **Multimodal Calibration:**
               - As formulated in Blueprint Section 4:
                 \\[ S = w_s S_{\\text{semantic}} + w_k S_{\\text{skills}} + w_e S_{\\text{evidence}} \\]
                 Combining contextual embeddings with deterministic taxonomy-based skill extraction ensures high recall without sacrificing precision.
            """)

# ==============================================================================
# TAB 5: SCREENING HISTORY & DATABASE
# ==============================================================================
with tab_history:
    st.markdown("### 📜 Screening History & Database")
    st.caption("Persistent SQLite storage tracking past screening runs, candidate cohorts, and weighted score configurations.")

    recent_runs = get_recent_runs(limit=15)
    if not recent_runs:
        st.info("No saved runs found in SQLite database. Run a screening on the first tab to record history.")
    else:
        st.markdown(f"**Total Historical Runs Recorded:** `{len(recent_runs)}`")
        run_options = {
            f"Run #{r['id']} - {r['job_title']} ({r['created_at'][:16]})": r['id']
            for r in recent_runs
        }
        selected_run_label = st.selectbox("Select Historical Screening Run to Inspect:", list(run_options.keys()))
        selected_run_id = run_options[selected_run_label]

        run_results = get_run_results(selected_run_id)

        if run_results:
            st.markdown(f"#### Ranked Candidates for Run #{selected_run_id}")
            hist_rows = []
            for rank, r in enumerate(run_results, 1):
                hist_rows.append({
                    "Rank": f"#{rank}",
                    "Candidate Name": r["candidate_name"],
                    "Fit Score": f"{r['final_score']}%",
                    "Tier": r["tier"],
                    "Semantic Score": f"{r['semantic_score']}%",
                    "Skills Score": f"{r['skills_score']}%",
                    "Evidence Score": f"{r['evidence_score']}%",
                    "Filename": r["filename"]
                })
            st.dataframe(pd.DataFrame(hist_rows), use_container_width=True)
