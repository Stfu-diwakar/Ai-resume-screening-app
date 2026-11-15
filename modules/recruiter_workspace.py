"""Recruiter ATS workspace for HireSense AI.

A lightweight, SQLite-backed applicant workflow layered on top of the existing
resume parser and matching engine. AI scores are decision-support signals only.
"""
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from config import DB_PATH, SAMPLE_RESUMES_DIR, SAMPLE_JOBS_DIR
from modules.parser import parse_resume, parse_job_description
from modules.semantic_matcher import SemanticMatcher


PIPELINE = ["Applied", "Shortlisted", "Interview", "Offer", "Rejected"]
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def init_ats_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ats_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                name TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                skills_json TEXT NOT NULL DEFAULT '[]',
                experience REAL NOT NULL DEFAULT 0,
                tenth REAL,
                twelfth REAL,
                cgpa REAL,
                graduation_year INTEGER,
                profile_json TEXT NOT NULL,
                stage TEXT NOT NULL DEFAULT 'Applied',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ats_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ats_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                event TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(candidate_id) REFERENCES ats_candidates(id)
            )
        """)


def _first_number(patterns, text, maximum=100):
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            try:
                value = float(match.group(1))
                if 0 <= value <= maximum:
                    return value
            except (ValueError, TypeError):
                pass
    return None


def _academic_fields(text):
    tenth = _first_number([
        r'(?:10th|class\s*x(?!i)|ssc|secondary)[^\n]{0,35}?(\d{2}(?:\.\d{1,2})?)\s*%',
        r'(\d{2}(?:\.\d{1,2})?)\s*%[^\n]{0,25}?(?:10th|class\s*x|ssc)'
    ], text)
    twelfth = _first_number([
        r'(?:12th|class\s*xii|class\s*12|hsc|senior\s+secondary)[^\n]{0,35}?(\d{2}(?:\.\d{1,2})?)\s*%',
        r'(\d{2}(?:\.\d{1,2})?)\s*%[^\n]{0,25}?(?:12th|class\s*xii|hsc)'
    ], text)
    cgpa = _first_number([
        r'(?:cgpa|cumulative\s+grade\s+point\s+average)[^\n]{0,20}?(\d(?:\.\d{1,2})?)',
        r'(\d(?:\.\d{1,2})?)\s*/\s*10\s*(?:cgpa)?'
    ], text, 10)
    years = re.findall(r'\b(?:20[0-3]\d)\b', text)
    grad_year = int(years[-1]) if years else None
    location = None
    for line in text.splitlines()[:18]:
        if re.search(r'\b(location|based in|address|city)\b', line, re.I):
            location = re.sub(r'(?i)\b(location|based in|address|city)\s*[:|-]?\s*', '', line).strip()[:80]
            break
    return {"tenth": tenth, "twelfth": twelfth, "cgpa": cgpa,
            "graduation_year": grad_year, "location": location}


def _profile_from_upload(upload):
    raw = upload.getvalue()
    profile = parse_resume(raw, upload.name)
    profile.update(_academic_fields(profile.get("full_text", "")))
    profile["skills"] = profile.get("skills") or []
    profile["experience_years"] = float(profile.get("experience_years") or 0)
    profile["candidate_name"] = profile.get("candidate_name") or Path(upload.name).stem
    return profile, hashlib.sha256(raw).hexdigest()


def _save_candidate(profile, fingerprint):
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        existing = conn.execute(
            "SELECT id FROM ats_candidates WHERE fingerprint=? OR "
            "(? IS NOT NULL AND email IS NOT NULL AND lower(email)=lower(?)) LIMIT 1",
            (fingerprint, profile.get("email"), profile.get("email"))
        ).fetchone()
        if existing:
            return False
        cur = conn.execute("""
            INSERT OR IGNORE INTO ats_candidates
            (fingerprint, filename, name, email, phone, location, skills_json,
             experience, tenth, twelfth, cgpa, graduation_year, profile_json,
             stage, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Applied', ?, ?)
        """, (fingerprint, profile.get("filename", ""), profile.get("candidate_name"),
              profile.get("email"), profile.get("phone"), profile.get("location"),
              json.dumps(profile.get("skills", [])), profile.get("experience_years", 0),
              profile.get("tenth"), profile.get("twelfth"), profile.get("cgpa"),
              profile.get("graduation_year"), json.dumps(profile), now, now))
        return cur.rowcount == 1


def _load_candidates():
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM ats_candidates ORDER BY updated_at DESC").fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["skills"] = json.loads(item.pop("skills_json") or "[]")
        item["profile"] = json.loads(item.pop("profile_json") or "{}")
        output.append(item)
    return output


def _save_job(title, description):
    with _connect() as conn:
        cur = conn.execute("INSERT INTO ats_jobs(title, description, created_at) VALUES (?, ?, ?)",
                           (title.strip(), description.strip(), datetime.now().isoformat(timespec="seconds")))
        return cur.lastrowid


def _load_jobs():
    with _connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM ats_jobs ORDER BY id DESC").fetchall()]


def _update_stage(candidate_id, stage, note=""):
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute("UPDATE ats_candidates SET stage=?, updated_at=? WHERE id=?",
                     (stage, now, candidate_id))
        conn.execute("INSERT INTO ats_activity(candidate_id,event,note,created_at) VALUES (?,?,?,?)",
                     (candidate_id, stage, note, now))


@st.cache_resource(show_spinner=False)
def _get_ats_matcher():
    return SemanticMatcher(model_name="all-MiniLM-L6-v2")


def _score(profile, job):
    jd = parse_job_description(job["description"], job["title"])
    candidate_skills = {s.lower() for s in profile.get("skills", [])}
    required = jd.get("required_skills", [])
    preferred = jd.get("preferred_skills", [])
    req = {s.lower() for s in required}
    pref = {s.lower() for s in preferred}
    req_match = [s for s in required if s.lower() in candidate_skills]
    pref_match = [s for s in preferred if s.lower() in candidate_skills]
    req_cov = len(req_match) / len(req) if req else 1.0
    pref_cov = len(pref_match) / len(pref) if pref else 1.0
    skill_score = (0.8 * req_cov + 0.2 * pref_cov) if req and pref else (req_cov if req else pref_cov)
    matcher = _get_ats_matcher()
    semantic = matcher.calculate_similarity(job["description"], profile.get("full_text", ""))
    exp_required = float(jd.get("min_experience_years") or 0)
    exp = float(profile.get("experience_years") or 0)
    exp_score = min(exp / exp_required, 1.0) if exp_required else 1.0
    total = round((0.35 * semantic + 0.50 * skill_score + 0.15 * exp_score) * 100, 1)
    return {"score": total, "semantic": round(semantic*100, 1),
            "skills": round(skill_score*100, 1), "experience": round(exp_score*100, 1),
            "matched": req_match + pref_match,
            "missing": [s for s in required if s.lower() not in candidate_skills],
            "preferred_missing": [s for s in preferred if s.lower() not in candidate_skills]}


def render_recruiter_workspace():
    init_ats_db()
    st.markdown("## Recruiter workspace")
    st.caption("A practical hiring desk: import candidates, match them to a role, shortlist, and move them through your pipeline.")
    jobs = _load_jobs()
    candidates = _load_candidates()

    metric_cols = st.columns(4)
    counts = {stage: sum(c["stage"] == stage for c in candidates) for stage in PIPELINE}
    for col, label, value in zip(metric_cols, ["Total candidates", "Shortlisted", "In interview", "Offers"], 
                                 [len(candidates), counts["Shortlisted"], counts["Interview"], counts["Offer"]]):
        col.metric(label, value)

    tabs = st.tabs(["Overview & ranking", "Import resumes", "Jobs", "Pipeline", "Compare & export"])

    with tabs[0]:
        if not jobs:
            st.info("Create a job description in the Jobs tab, then rank candidates against it.")
        else:
            job_labels = {f'{j["title"]} · #{j["id"]}': j for j in jobs}
            selected_job = st.selectbox("Active job", list(job_labels), key="ats_active_job")
            job = job_labels[selected_job]
            st.caption(f'Role created {job["created_at"][:10]} · {len(candidates)} candidate profiles')
            scored = []
            for c in candidates:
                result = _score(c["profile"], job)
                scored.append({**c, **result})
            f1, f2, f3, f4 = st.columns(4)
            min_score = f1.slider("Minimum match", 0, 100, 0, key="ats_min_score")
            stage_filter = f2.multiselect("Pipeline stage", PIPELINE, default=PIPELINE, key="ats_stage_filter")
            skill_query = f3.text_input("Skill contains", key="ats_skill_filter")
            location_query = f4.text_input("Location contains", key="ats_location_filter")
            a1, a2, a3 = st.columns(3)
            min_exp = a1.number_input("Minimum experience (years)", min_value=0.0, max_value=40.0, value=0.0, step=1.0)
            min_tenth = a2.number_input("10th minimum (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
            min_twelfth = a3.number_input("12th minimum (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
            b1, b2, b3 = st.columns(3)
            min_cgpa = b1.number_input("Minimum CGPA (10-point scale)", min_value=0.0, max_value=10.0, value=0.0, step=0.5)
            grad_from = b2.number_input("Graduation year from", min_value=2000, max_value=2035, value=2000)
            grad_to = b3.number_input("Graduation year to", min_value=2000, max_value=2035, value=2035)
            filtered = []
            for c in scored:
                if c["score"] < min_score or c["stage"] not in stage_filter: continue
                if float(c["experience"] or 0) < min_exp: continue
                if min_tenth and (c["tenth"] is None or c["tenth"] < min_tenth): continue
                if min_twelfth and (c["twelfth"] is None or c["twelfth"] < min_twelfth): continue
                if min_cgpa and (c["cgpa"] is None or c["cgpa"] < min_cgpa): continue
                if c["graduation_year"] and not (grad_from <= c["graduation_year"] <= grad_to): continue
                if skill_query and not any(skill_query.lower() in s.lower() for s in c["skills"]): continue
                if location_query and location_query.lower() not in (c["location"] or "").lower(): continue
                filtered.append(c)
            filtered.sort(key=lambda x: x["score"], reverse=True)
            st.markdown(f"### Ranked candidates · {len(filtered)} shown")
            if filtered:
                table = pd.DataFrame([{"Rank": i, "Candidate": c["name"], "Match": c["score"],
                    "Stage": c["stage"], "Skills": ", ".join(c["skills"][:8]),
                    "Experience (yrs)": c["experience"], "10th %": c["tenth"],
                    "12th %": c["twelfth"], "CGPA": c["cgpa"], "Graduation": c["graduation_year"],
                    "Location": c["location"] or "—"} for i,c in enumerate(filtered,1)])
                st.dataframe(table, use_container_width=True, hide_index=True)
                selected_id = st.selectbox("Inspect candidate", [c["id"] for c in filtered],
                    format_func=lambda cid: next(f'{x["name"]} · {x["score"]}%' for x in filtered if x["id"] == cid))
                chosen = next(c for c in filtered if c["id"] == selected_id)
                left, right = st.columns([1.2, 1])
                with left:
                    st.markdown(f'### {chosen["name"]}')
                    st.caption(f'{chosen["email"] or "No email"} · {chosen["location"] or "Location not parsed"}')
                    st.metric("Role match", f'{chosen["score"]}%')
                    st.progress(chosen["score"]/100)
                    st.write(f'**Matched skills:** {", ".join(chosen["matched"]) or "None detected"}')
                    st.write(f'**Skill gaps:** {", ".join(chosen["missing"]) or "No required skill gaps detected"}')
                    st.write(f'**Additional gaps:** {", ".join(chosen["preferred_missing"]) or "None"}')
                with right:
                    st.markdown("#### Score breakdown")
                    st.write(f'Semantic similarity: **{chosen["semantic"]}%**')
                    st.write(f'Skill coverage: **{chosen["skills"]}%**')
                    st.write(f'Experience alignment: **{chosen["experience"]}%**')
                    st.caption("Scores are heuristic decision-support signals. Review the original resume before making a decision.")
                    new_stage = st.selectbox("Move candidate to", PIPELINE, index=PIPELINE.index(chosen["stage"]), key=f'ats_stage_{chosen["id"]}')
                    if st.button("Update pipeline stage", key=f'ats_update_{chosen["id"]}'):
                        _update_stage(chosen["id"], new_stage, f'Updated from ranking view for {job["title"]}')
                        st.success("Candidate stage updated.")
                        st.rerun()
            else:
                st.warning("No candidates match these filters. Try relaxing one or more criteria.")

    with tabs[1]:
        st.markdown("### Bulk resume intake")
        st.write("Upload multiple PDF or DOCX resumes at once. Duplicate files are detected using a SHA-256 fingerprint.")
        uploads = st.file_uploader("Choose resumes", type=["pdf", "docx"], accept_multiple_files=True, key="ats_bulk_upload")
        if uploads and st.button(f"Parse and import {len(uploads)} resume(s)", type="primary"):
            added, duplicates, errors = 0, 0, []
            progress = st.progress(0)
            for index, upload in enumerate(uploads):
                try:
                    profile, fingerprint = _profile_from_upload(upload)
                    if not profile.get("full_text", "").strip():
                        errors.append(f"{upload.name}: no readable text found (scanned PDFs may need OCR).")
                    elif _save_candidate(profile, fingerprint):
                        added += 1
                    else:
                        duplicates += 1
                except Exception as exc:
                    errors.append(f"{upload.name}: {exc}")
                progress.progress((index+1)/len(uploads))
            st.success(f"Imported {added} new profile(s); skipped {duplicates} duplicate(s).")
            for error in errors: st.warning(error)
            st.rerun()
        if st.button("Load included demo resume dataset", key="ats_load_demo"):
            demo_files = sorted(SAMPLE_RESUMES_DIR.glob("*.docx")) + sorted(SAMPLE_RESUMES_DIR.glob("*.pdf"))
            # Prefer one document per candidate; the same person may have PDF and DOCX copies.
            unique_files = {}
            for path in demo_files:
                unique_files.setdefault(path.stem, path)
            added_demo, duplicate_demo, demo_errors = 0, 0, []
            for path in unique_files.values():
                try:
                    profile, fingerprint = _profile_from_upload(type("LocalUpload", (), {
                        "getvalue": lambda self, p=path: p.read_bytes(),
                        "name": path.name
                    })())
                    if _save_candidate(profile, fingerprint):
                        added_demo += 1
                    else:
                        duplicate_demo += 1
                except Exception as exc:
                    demo_errors.append(f"{path.name}: {exc}")
            st.success(f"Demo dataset: {added_demo} added, {duplicate_demo} already present.")
            for error in demo_errors:
                st.warning(error)
            st.rerun()
        st.caption("Academic fields are extracted only when clearly labelled; missing values remain blank rather than being guessed.")

    with tabs[2]:
        st.markdown("### Job descriptions")
        with st.form("ats_create_job"):
            title = st.text_input("Job title", placeholder="e.g. Python Developer")
            description = st.text_area("Full job description", height=220, placeholder="Paste responsibilities, required skills, preferred skills and experience...")
            submitted = st.form_submit_button("Save job description", type="primary")
        if submitted:
            if not title.strip() or not description.strip():
                st.error("Add both a job title and description.")
            else:
                _save_job(title, description)
                st.success("Job description saved.")
                st.rerun()
        if st.button("Import included sample job descriptions", key="ats_import_sample_jobs"):
            imported = 0
            for path in sorted(SAMPLE_JOBS_DIR.glob("*.txt")):
                description = path.read_text(encoding="utf-8")
                title = re.sub(r"^job_", "", path.stem).replace("_", " ").title()
                if description.strip():
                    _save_job(title, description)
                    imported += 1
            st.success(f"Imported {imported} sample job description(s).")
            st.rerun()
        if jobs:
            st.markdown("#### Saved roles")
            for job_item in jobs:
                with st.expander(f'{job_item["title"]} · #{job_item["id"]}'):
                    st.write(job_item["description"])
                    st.caption(f'Created {job_item["created_at"][:16]}')

    with tabs[3]:
        st.markdown("### Hiring pipeline")
        st.caption("Move applicants through a consistent, auditable hiring process.")
        if not candidates:
            st.info("Import resumes to populate the pipeline.")
        else:
            for stage in PIPELINE:
                group = [c for c in candidates if c["stage"] == stage]
                with st.expander(f"{stage} · {len(group)}", expanded=stage in ["Applied", "Shortlisted"]):
                    if not group:
                        st.caption("No candidates in this stage.")
                    for c in group:
                        c1, c2, c3 = st.columns([2, 2, 1])
                        c1.write(f'**{c["name"]}**')
                        c2.caption(c["email"] or c["filename"])
                        next_stage = c3.selectbox("Stage", PIPELINE, index=PIPELINE.index(stage), key=f'pipe_{c["id"]}', label_visibility="collapsed")
                        if next_stage != stage:
                            _update_stage(c["id"], next_stage)
                            st.rerun()

    with tabs[4]:
        st.markdown("### Candidate comparison")
        if len(candidates) < 2:
            st.info("Import at least two resumes to compare profiles.")
        else:
            labels = {f'{c["name"]} · {c["filename"]}': c for c in candidates}
            chosen_labels = st.multiselect("Select up to three candidates", list(labels), max_selections=3)
            if len(chosen_labels) >= 2:
                compare = []
                for label in chosen_labels:
                    c = labels[label]
                    compare.append({"Candidate": c["name"], "Email": c["email"], "Stage": c["stage"],
                        "Experience (years)": c["experience"], "10th %": c["tenth"], "12th %": c["twelfth"],
                        "CGPA": c["cgpa"], "Graduation year": c["graduation_year"],
                        "Location": c["location"], "Skills": ", ".join(c["skills"])})
                st.dataframe(pd.DataFrame(compare).T.rename_axis("Attribute").reset_index(),
                             use_container_width=True, hide_index=True)
        if candidates:
            export_rows = [{"Name": c["name"], "Email": c["email"], "Phone": c["phone"],
                "Location": c["location"], "Experience": c["experience"], "10th %": c["tenth"],
                "12th %": c["twelfth"], "CGPA": c["cgpa"], "Graduation year": c["graduation_year"],
                "Stage": c["stage"], "Skills": ", ".join(c["skills"]), "Resume": c["filename"]} for c in candidates]
            csv_data = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8")
            st.download_button("Download candidate database (CSV)", csv_data, "hiresense_candidates.csv", "text/csv")
            recipients = [c["email"] for c in candidates if c["stage"] == "Shortlisted" and c["email"]]
            if recipients:
                st.markdown("#### Shortlisted candidate communication")
                st.caption(f"{len(recipients)} shortlisted email address(es) detected.")
                st.code("; ".join(recipients))
                st.info("Copy the addresses into your approved mail client. This app does not send email or expose candidate addresses to third-party services.")
