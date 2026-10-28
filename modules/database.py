"""
SQLite Database Layer for Screening History and Persistent Storage
"""
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Create and return a database connection with dict row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            full_text TEXT NOT NULL,
            required_skills TEXT,
            preferred_skills TEXT,
            min_experience REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Candidates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            candidate_name TEXT,
            email TEXT,
            phone TEXT,
            linkedin TEXT,
            github TEXT,
            skills TEXT,
            experience_years REAL,
            full_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Screening runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            job_title TEXT,
            run_name TEXT,
            weights_json TEXT,
            total_candidates INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    """)

    # Screening results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            candidate_name TEXT,
            filename TEXT,
            final_score REAL,
            tier TEXT,
            semantic_score REAL,
            skills_score REAL,
            evidence_score REAL,
            details_json TEXT,
            FOREIGN KEY (run_id) REFERENCES screening_runs (id)
        )
    """)

    conn.commit()
    conn.close()

def save_job(parsed_job: Dict[str, Any]) -> int:
    """Insert a job description and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (title, full_text, required_skills, preferred_skills, min_experience)
        VALUES (?, ?, ?, ?, ?)
    """, (
        parsed_job.get("title", "Job Description"),
        parsed_job.get("full_text", ""),
        json.dumps(parsed_job.get("required_skills", [])),
        json.dumps(parsed_job.get("preferred_skills", [])),
        parsed_job.get("min_experience_years", 0.0)
    ))
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id

def save_screening_run(
    job_title: str,
    job_id: Optional[int],
    weights: Dict[str, float],
    ranked_candidates: List[Dict[str, Any]],
    run_name: Optional[str] = None
) -> int:
    """Save an entire screening run and its candidate rankings."""
    if not run_name:
        run_name = f"Screening - {datetime.now().strftime('%b %d, %H:%M')}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO screening_runs (job_id, job_title, run_name, weights_json, total_candidates)
        VALUES (?, ?, ?, ?, ?)
    """, (
        job_id,
        job_title,
        run_name,
        json.dumps(weights),
        len(ranked_candidates)
    ))
    run_id = cursor.lastrowid

    for cand in ranked_candidates:
        score_data = cand.get("score_data", {})
        comp = score_data.get("components", {})
        cursor.execute("""
            INSERT INTO screening_results (
                run_id, candidate_name, filename, final_score, tier,
                semantic_score, skills_score, evidence_score, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            cand.get("candidate_name", "Unknown"),
            cand.get("filename", ""),
            score_data.get("final_score", 0.0),
            score_data.get("tier", ""),
            comp.get("semantic_score", 0.0),
            comp.get("skills_score", 0.0),
            comp.get("evidence_score", 0.0),
            json.dumps({
                "skill_details": score_data.get("skill_details", {}),
                "evidence_details": score_data.get("evidence_details", {}),
                "explanation": cand.get("explanation", "")
            })
        ))

    conn.commit()
    conn.close()
    return run_id

def get_recent_runs(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve historical screening runs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, job_title, run_name, weights_json, total_candidates, created_at
        FROM screening_runs
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_run_results(run_id: int) -> List[Dict[str, Any]]:
    """Retrieve candidate results for a given screening run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM screening_results
        WHERE run_id = ?
        ORDER BY final_score DESC
    """, (run_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        item = dict(r)
        if item.get("details_json"):
            try:
                item["details"] = json.loads(item["details_json"])
            except Exception:
                item["details"] = {}
        results.append(item)
    return results

# Initialize DB on module load
init_db()
