"""
Comprehensive Unit & Integration Test Suite for HireSense AI
"""
from pathlib import Path
from modules.parser import parse_resume, parse_job_description
from modules.semantic_matcher import SemanticMatcher, TfidfBaseline
from modules.scoring import calculate_candidate_score
from modules.explainable_ai import generate_natural_language_explanation, prepare_radar_chart_data
from modules.recommender import generate_recommendations
from modules.academic_eval import run_academic_benchmark
from modules.database import get_recent_runs, save_job, save_screening_run

def test_full_pipeline():
    print("=== TEST 1: Parsing PDF & DOCX Resumes ===")
    sample_pdf = Path("data/sample_resumes/alex_morgan_senior_ml.pdf")
    sample_docx = Path("data/sample_resumes/sarah_lin_fullstack.docx")

    assert sample_pdf.exists(), "Sample PDF not found!"
    assert sample_docx.exists(), "Sample DOCX not found!"

    cand_ml = parse_resume(sample_pdf.read_bytes(), sample_pdf.name)
    print(f"Parsed PDF: {cand_ml['candidate_name']} | Skills count: {len(cand_ml['skills'])} | Years: {cand_ml['experience_years']}")
    assert len(cand_ml['skills']) > 0, "No skills extracted from PDF"

    cand_fs = parse_resume(sample_docx.read_bytes(), sample_docx.name)
    print(f"Parsed DOCX: {cand_fs['candidate_name']} | Skills count: {len(cand_fs['skills'])} | Years: {cand_fs['experience_years']}")
    assert len(cand_fs['skills']) > 0, "No skills extracted from DOCX"

    print("\n=== TEST 2: Parsing Job Description ===")
    job_path = Path("data/sample_jobs/job_senior_ml_engineer.txt")
    job_data = parse_job_description(job_path.read_text(encoding="utf-8"), title="Senior ML Engineer")
    print(f"Parsed Job: {job_data['title']} | Required skills: {job_data['required_skills']}")
    assert len(job_data['required_skills']) > 0

    print("\n=== TEST 3: Semantic Matching & S-BERT Embeddings ===")
    matcher = SemanticMatcher()
    sim_ml = matcher.calculate_similarity(job_data["full_text"], cand_ml["full_text"])
    sim_fs = matcher.calculate_similarity(job_data["full_text"], cand_fs["full_text"])
    print(f"Semantic Sim (Senior ML Candidate): {sim_ml*100:.1f}%")
    print(f"Semantic Sim (Full Stack Candidate): {sim_fs*100:.1f}%")
    assert sim_ml > sim_fs, "Senior ML candidate should have higher similarity for ML role!"

    print("\n=== TEST 4: Multimodal Scoring ===")
    evidence = matcher.find_top_evidence(
        ["Expertise in PyTorch and Hugging Face Transformers", "FastAPI and Docker deployment"],
        cand_ml["full_text"]
    )
    score_ml = calculate_candidate_score(cand_ml, job_data, sim_ml, evidence)
    print(f"Alex Morgan Fit Score: {score_ml['final_score']}% ({score_ml['tier']})")
    assert score_ml['final_score'] >= 75.0, "Alex Morgan should score in strong match tier!"

    print("\n=== TEST 5: Explainable AI & Recommendations ===")
    explanation = generate_natural_language_explanation(cand_ml["candidate_name"], score_ml, cand_ml["skills"])
    print("Explanation preview:")
    print(explanation[:200] + "...")

    radar = prepare_radar_chart_data(score_ml)
    print(f"Radar Categories: {radar['categories']}")
    print(f"Radar Values: {radar['values']}")

    recs = generate_recommendations(
        score_ml["skill_details"]["missing_required"],
        score_ml["skill_details"]["missing_preferred"],
        target_role=job_data["title"]
    )
    print(f"Generated Roadmap stages: {len(recs['learning_roadmap_stages'])} | Projects: {len(recs['recommended_projects'])}")

    print("\n=== TEST 6: Academic Benchmark (S-BERT vs TF-IDF) ===")
    bench = run_academic_benchmark()
    print("Metrics summary:")
    print("S-BERT NDCG@3:", bench["metrics_summary"]["S-BERT"]["NDCG@3"])
    print("TF-IDF NDCG@3:", bench["metrics_summary"]["TF-IDF"]["NDCG@3"])
    assert bench["metrics_summary"]["S-BERT"]["NDCG@3"] >= bench["metrics_summary"]["TF-IDF"]["NDCG@3"]

    print("\n=== TEST 7: SQLite Database Storage ===")
    job_id = save_job(job_data)
    run_id = save_screening_run(job_data["title"], job_id, {"semantic": 0.4, "skills": 0.4, "evidence": 0.2}, [
        {**cand_ml, "score_data": score_ml, "explanation": explanation}
    ])
    recent = get_recent_runs()
    print(f"Saved run #{run_id} | Total runs in DB: {len(recent)}")
    assert len(recent) > 0

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_full_pipeline()
