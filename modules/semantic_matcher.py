"""
Semantic Embeddings and Similarity Matching Engine
Supports:
1. Sentence-BERT (all-MiniLM-L6-v2) embedding & cosine similarity
2. Chunk/Sentence-level contextual evidence extraction
3. TF-IDF Baseline vectorizer for academic benchmarking
"""
import re
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Global model cache
_SBERT_MODEL = None
_SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
_SBERT_LOAD_ERROR = None

def get_sentence_transformer_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load or retrieve cached SentenceTransformer instance."""
    global _SBERT_MODEL, _SBERT_MODEL_NAME, _SBERT_LOAD_ERROR
    if _SBERT_MODEL is not None and _SBERT_MODEL_NAME == model_name:
        return _SBERT_MODEL

    try:
        import os
        from sentence_transformers import SentenceTransformer
        # Try local cache first to avoid slow network timeouts
        try:
            _SBERT_MODEL = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            _SBERT_MODEL = SentenceTransformer(model_name)

        _SBERT_MODEL_NAME = model_name
        _SBERT_LOAD_ERROR = None
        return _SBERT_MODEL
    except Exception as e:
        _SBERT_LOAD_ERROR = str(e)
        return None

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two 1D or 2D vectors."""
    if vec1 is None or vec2 is None:
        return 0.0
    v1 = np.atleast_2d(vec1)
    v2 = np.atleast_2d(vec2)
    sim = cosine_similarity(v1, v2)[0][0]
    return float(np.clip(sim, 0.0, 1.0))

class SemanticMatcher:
    """
    Semantic Matcher using Sentence-BERT embeddings.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = get_sentence_transformer_model(model_name)

    def is_available(self) -> bool:
        return self.model is not None

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode a list of texts into dense vectors."""
        if not self.is_available():
            raise RuntimeError(f"SentenceTransformer not available: {_SBERT_LOAD_ERROR}")
        return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Compute contextual cosine similarity between two texts."""
        if not self.is_available():
            # Fallback to TF-IDF similarity if S-BERT is not loaded
            baseline = TfidfBaseline()
            return baseline.calculate_similarity(text1, text2)

        if not text1.strip() or not text2.strip():
            return 0.0

        embeddings = self.encode([text1, text2])
        return compute_cosine_similarity(embeddings[0], embeddings[1])

    def find_top_evidence(self, jd_sentences: List[str], resume_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find specific sentences or bullet points in the resume that best match
        the key requirements in the job description.
        """
        if not resume_text.strip() or not jd_sentences:
            return []

        # Split resume into clean sentences/bullets
        resume_units = [
            s.strip() for s in re.split(r'\n+|•|;|\.\s+', resume_text)
            if len(s.strip()) > 25 and not s.strip().startswith(('http', 'www', 'Email', 'Phone'))
        ]

        if not resume_units:
            return []

        evidence_results = []

        if self.is_available():
            try:
                jd_emb = self.encode(jd_sentences)
                res_emb = self.encode(resume_units)
                # Compute matrix similarity (len(jd_sentences) x len(resume_units))
                sim_matrix = cosine_similarity(jd_emb, res_emb)

                for i, jd_sent in enumerate(jd_sentences):
                    best_indices = np.argsort(sim_matrix[i])[::-1][:top_k]
                    matches = []
                    for idx in best_indices:
                        score = float(sim_matrix[i][idx])
                        if score >= 0.35:  # Relevance threshold
                            matches.append({
                                "text": resume_units[idx],
                                "similarity": round(score * 100, 1)
                            })
                    if matches:
                        evidence_results.append({
                            "requirement": jd_sent,
                            "top_matches": matches,
                            "best_similarity": matches[0]["similarity"]
                        })
                return evidence_results
            except Exception:
                pass

        # Fallback keyword matching for evidence
        for jd_sent in jd_sentences[:5]:
            req_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', jd_sent.lower()))
            scored = []
            for unit in resume_units:
                unit_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', unit.lower()))
                overlap = len(req_words & unit_words)
                if overlap > 1:
                    score = min(overlap / max(len(req_words), 1), 1.0) * 100
                    scored.append({"text": unit, "similarity": round(score, 1)})
            if scored:
                scored.sort(key=lambda x: x["similarity"], reverse=True)
                evidence_results.append({
                    "requirement": jd_sent,
                    "top_matches": scored[:top_k],
                    "best_similarity": scored[0]["similarity"]
                })

        return evidence_results


class TfidfBaseline:
    """
    Classic TF-IDF + Cosine Similarity Baseline.
    Used for academic comparison against S-BERT.
    """
    def __init__(self, ngram_range=(1, 2), max_features=5000):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=ngram_range,
            max_features=max_features
        )

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Compute TF-IDF cosine similarity between two texts."""
        if not text1.strip() or not text2.strip():
            return 0.0
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(np.clip(sim, 0.0, 1.0))
        except Exception:
            return 0.0

    def calculate_batch_similarities(self, jd_text: str, resume_texts: List[str]) -> List[float]:
        """Compute TF-IDF cosine similarity for one JD against multiple resumes."""
        if not resume_texts:
            return []
        corpus = [jd_text] + resume_texts
        try:
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            jd_vec = tfidf_matrix[0:1]
            resume_vecs = tfidf_matrix[1:]
            sims = cosine_similarity(jd_vec, resume_vecs)[0]
            return [float(np.clip(s, 0.0, 1.0)) for s in sims]
        except Exception:
            return [0.0] * len(resume_texts)
