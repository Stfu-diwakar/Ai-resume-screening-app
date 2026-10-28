"""
Academic Evaluation and Benchmarking Module
Compares Semantic Matching (Sentence-BERT) vs Classic Lexical Baseline (TF-IDF).
Calculates IR metrics: Precision@K, Recall@K, F1, MRR, NDCG@K,
Vocabulary Mismatch Robustness, and Inference Latency.
"""
import time
from typing import Any, Dict, List, Tuple
import numpy as np
from scipy.stats import spearmanr, pearsonr
from modules.semantic_matcher import SemanticMatcher, TfidfBaseline

# Benchmark test cases evaluating Semantic Understanding vs Lexical Overlap
BENCHMARK_SYNONYM_PAIRS = [
    {
        "query": "Experienced with deep neural networks and NLP models",
        "doc": "Designed and deployed BERT and Transformer architectures in PyTorch",
        "ground_truth_relevance": 1.0,
        "concept": "NLP / Deep Learning Terminology"
    },
    {
        "query": "Proficient in container orchestration and Kubernetes",
        "doc": "Managed production K8s clusters and Helm charts for microservices",
        "ground_truth_relevance": 1.0,
        "concept": "Kubernetes / K8s Abbreviation"
    },
    {
        "query": "Hands-on experience with Golang backend development",
        "doc": "5 years building high-concurrency microservices using Go and gRPC",
        "ground_truth_relevance": 1.0,
        "concept": "Golang vs Go Alias"
    },
    {
        "query": "Relational database schema optimization and indexing",
        "doc": "Tuned complex PostgreSQL queries, created partition keys and b-tree indexes",
        "ground_truth_relevance": 1.0,
        "concept": "PostgreSQL as Relational Database"
    },
    {
        "query": "Implemented continuous integration and deployment pipelines",
        "doc": "Automated test suites and cloud delivery workflows using GitHub Actions",
        "ground_truth_relevance": 1.0,
        "concept": "CI/CD vs GitHub Actions"
    },
    {
        "query": "Financial accountant with IFRS compliance experience",
        "doc": "Senior full-stack Python software developer specialized in React and AWS",
        "ground_truth_relevance": 0.0,
        "concept": "Negative Irrelevant Baseline"
    }
]

# Benchmark Candidate Profiles with Ground Truth Relevance for a Senior ML Engineer role
BENCHMARK_PROFILES = [
    {
        "id": "c1",
        "name": "Sarah Chen",
        "label": "Strong Senior ML Engineer",
        "ground_truth_relevance": 3,  # 3: Highly relevant, 2: Relevant, 1: Weak, 0: Irrelevant
        "ground_truth_binary": 1,
        "text": """Sarah Chen - Staff Machine Learning Engineer.
        Summary: 7+ years of experience leading ML initiatives. Expert in PyTorch, Transformers, LLM fine-tuning, and RAG architectures.
        Experience: Spearheaded large language model alignment, semantic search pipelines, and vector database deployments using ChromaDB and Milvus.
        Skills: Python, PyTorch, Hugging Face, NLP, Transformers, Docker, Kubernetes, AWS, PostgreSQL, FastAPI."""
    },
    {
        "id": "c2",
        "name": "David Miller",
        "label": "Intermediate Data Scientist",
        "ground_truth_relevance": 2,
        "ground_truth_binary": 1,
        "text": """David Miller - Senior Data Scientist.
        Summary: 4 years of experience applying machine learning models for predictive analytics.
        Experience: Built Scikit-Learn pipelines, XGBoost classification models, and automated reporting. Familiar with basic PyTorch.
        Skills: Python, Scikit-Learn, Pandas, NumPy, SQL, Git, Tableau, Docker."""
    },
    {
        "id": "c3",
        "name": "Elena Rostova",
        "label": "Full Stack Engineer (Minor ML exposure)",
        "ground_truth_relevance": 1,
        "ground_truth_binary": 0,
        "text": """Elena Rostova - Full Stack Web Developer.
        Summary: 5 years developing React frontends and Node.js backends. Built one prototype chatbot using OpenAI API.
        Experience: Developed microservices in Node and FastAPI, designed PostgreSQL schemas, integrated payment gateways.
        Skills: JavaScript, TypeScript, React, Next.js, Node.js, Python, PostgreSQL, Redis, Docker."""
    },
    {
        "id": "c4",
        "name": "Marcus Johnson",
        "label": "Cloud DevOps Engineer",
        "ground_truth_relevance": 1,
        "ground_truth_binary": 0,
        "text": """Marcus Johnson - Cloud Infrastructure Architect.
        Summary: 6 years managing AWS and Kubernetes clusters.
        Experience: Implemented CI/CD pipelines, Terraform automation, and Prometheus monitoring. No machine learning experience.
        Skills: AWS, Kubernetes, Docker, Terraform, Linux, Bash, CI/CD, Python."""
    },
    {
        "id": "c5",
        "name": "Emily Taylor",
        "label": "Junior Marketing Specialist",
        "ground_truth_relevance": 0,
        "ground_truth_binary": 0,
        "text": """Emily Taylor - Digital Marketing Associate.
        Summary: 2 years in content marketing, SEO copywriting, social media campaigns, and Google Analytics.
        Skills: SEO, Copywriting, Google Ads, Content Strategy, Canva, Social Media."""
    }
]

BENCHMARK_JOB = """Senior Machine Learning Engineer (NLP & LLMs)
Requirements:
- 5+ years of experience developing machine learning models and NLP systems.
- Strong proficiency in Python, PyTorch, Transformers, Hugging Face, and semantic search.
- Hands-on experience with Large Language Models (LLMs), RAG pipelines, and vector databases.
- Containerization with Docker and deployment on AWS/Kubernetes.
- Bachelor's or Master's in Computer Science, Data Science, or related field."""

def compute_dcg(relevances: List[int], k: int) -> float:
    """Compute Discounted Cumulative Gain at K."""
    relevances = relevances[:k]
    dcg = 0.0
    for i, rel in enumerate(relevances):
        dcg += (2**rel - 1) / np.log2(i + 2)
    return dcg

def compute_ndcg(ranked_relevances: List[int], k: int = 3) -> float:
    """Compute Normalized Discounted Cumulative Gain at K."""
    dcg = compute_dcg(ranked_relevances, k)
    ideal_relevances = sorted(ranked_relevances, reverse=True)
    idcg = compute_dcg(ideal_relevances, k)
    if idcg == 0:
        return 0.0
    return float(dcg / idcg)

def run_academic_benchmark() -> Dict[str, Any]:
    """
    Run full academic comparison between Sentence-BERT and TF-IDF:
    1. Synonym/paraphrase robustness
    2. Ranking metrics (Spearman, Pearson, NDCG@3, P@1, P@3, MRR)
    3. Inference Latency
    """
    sbert_matcher = SemanticMatcher()
    tfidf_matcher = TfidfBaseline()

    # 1. Run Synonym / Lexical Gap Comparison
    synonym_results = []
    for pair in BENCHMARK_SYNONYM_PAIRS:
        s_sbert = sbert_matcher.calculate_similarity(pair["query"], pair["doc"])
        s_tfidf = tfidf_matcher.calculate_similarity(pair["query"], pair["doc"])
        synonym_results.append({
            "concept": pair["concept"],
            "query": pair["query"],
            "doc": pair["doc"],
            "sbert_score": round(s_sbert * 100, 1),
            "tfidf_score": round(s_tfidf * 100, 1),
            "advantage": round((s_sbert - s_tfidf) * 100, 1)
        })

    # 2. Run Candidate Ranking on Benchmark Dataset
    # Measure Latency
    t0 = time.perf_counter()
    sbert_scores = []
    for cand in BENCHMARK_PROFILES:
        s = sbert_matcher.calculate_similarity(BENCHMARK_JOB, cand["text"])
        sbert_scores.append(s)
    sbert_latency_ms = (time.perf_counter() - t0) * 1000 / len(BENCHMARK_PROFILES)

    t1 = time.perf_counter()
    tfidf_scores = tfidf_matcher.calculate_batch_similarities(
        BENCHMARK_JOB, [c["text"] for c in BENCHMARK_PROFILES]
    )
    tfidf_latency_ms = (time.perf_counter() - t1) * 1000 / len(BENCHMARK_PROFILES)

    # Ground truth relevances
    gt_graded = [c["ground_truth_relevance"] for c in BENCHMARK_PROFILES]
    gt_binary = [c["ground_truth_binary"] for c in BENCHMARK_PROFILES]

    # Rank indices
    sbert_rank_idx = np.argsort(sbert_scores)[::-1]
    tfidf_rank_idx = np.argsort(tfidf_scores)[::-1]

    # Graded rankings
    sbert_ranked_gt = [gt_graded[i] for i in sbert_rank_idx]
    tfidf_ranked_gt = [gt_graded[i] for i in tfidf_rank_idx]

    # Binary rankings
    sbert_ranked_bin = [gt_binary[i] for i in sbert_rank_idx]
    tfidf_ranked_bin = [gt_binary[i] for i in tfidf_rank_idx]

    # NDCG@3
    ndcg_sbert = compute_ndcg(sbert_ranked_gt, k=3)
    ndcg_tfidf = compute_ndcg(tfidf_ranked_gt, k=3)

    # Precision@1, Precision@3
    p1_sbert = sbert_ranked_bin[0]
    p1_tfidf = tfidf_ranked_bin[0]

    p3_sbert = sum(sbert_ranked_bin[:3]) / 3.0
    p3_tfidf = sum(tfidf_ranked_bin[:3]) / 3.0

    # Mean Reciprocal Rank (MRR) - rank of first relevant doc
    def calc_mrr(ranked_bin):
        for rank, val in enumerate(ranked_bin, 1):
            if val == 1:
                return 1.0 / rank
        return 0.0

    mrr_sbert = calc_mrr(sbert_ranked_bin)
    mrr_tfidf = calc_mrr(tfidf_ranked_bin)

    # Rank correlation with ground truth
    spearman_sbert, _ = spearmanr(sbert_scores, gt_graded)
    spearman_tfidf, _ = spearmanr(tfidf_scores, gt_graded)

    pearson_sbert, _ = pearsonr(sbert_scores, gt_graded)
    pearson_tfidf, _ = pearsonr(tfidf_scores, gt_graded)

    # Per-candidate score comparison table
    candidate_comparisons = []
    for i, cand in enumerate(BENCHMARK_PROFILES):
        candidate_comparisons.append({
            "name": cand["name"],
            "label": cand["label"],
            "ground_truth_rank": sorted(gt_graded, reverse=True).index(cand["ground_truth_relevance"]) + 1,
            "sbert_score": round(sbert_scores[i] * 100, 1),
            "tfidf_score": round(tfidf_scores[i] * 100, 1),
            "sbert_rank": list(sbert_rank_idx).index(i) + 1,
            "tfidf_rank": list(tfidf_rank_idx).index(i) + 1
        })

    return {
        "metrics_summary": {
            "S-BERT": {
                "NDCG@3": round(ndcg_sbert, 3),
                "P@1": round(p1_sbert, 3),
                "P@3": round(p3_sbert, 3),
                "MRR": round(mrr_sbert, 3),
                "Spearman_rho": round(spearman_sbert, 3),
                "Pearson_r": round(pearson_sbert, 3),
                "Latency_ms": round(sbert_latency_ms, 1)
            },
            "TF-IDF": {
                "NDCG@3": round(ndcg_tfidf, 3),
                "P@1": round(p1_tfidf, 3),
                "P@3": round(p3_tfidf, 3),
                "MRR": round(mrr_tfidf, 3),
                "Spearman_rho": round(spearman_tfidf, 3),
                "Pearson_r": round(pearson_tfidf, 3),
                "Latency_ms": round(tfidf_latency_ms, 1)
            }
        },
        "synonym_tests": synonym_results,
        "candidate_comparisons": candidate_comparisons
    }
