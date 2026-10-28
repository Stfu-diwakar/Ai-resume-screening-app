"""
HireSense AI - Configuration Settings
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_RESUMES_DIR = DATA_DIR / "sample_resumes"
SAMPLE_JOBS_DIR = DATA_DIR / "sample_jobs"
DB_PATH = DATA_DIR / "hiresense.db"

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
SAMPLE_RESUMES_DIR.mkdir(exist_ok=True)
SAMPLE_JOBS_DIR.mkdir(exist_ok=True)

# Default Scoring Weights (Blueprint formula: S = w_s * S_semantic + w_k * S_skills + w_e * S_evidence)
DEFAULT_WEIGHT_SEMANTIC = 0.40
DEFAULT_WEIGHT_SKILLS = 0.40
DEFAULT_WEIGHT_EVIDENCE = 0.20

# Embedding model configurations
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
ALTERNATIVE_EMBEDDING_MODEL = "paraphrase-MiniLM-L3-v2"

# TF-IDF Baseline configuration
TFIDF_MAX_FEATURES = 5000
TFIDF_NGRAM_RANGE = (1, 2)
