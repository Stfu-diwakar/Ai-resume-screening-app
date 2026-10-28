# HireSense AI: Semantic Resume Screening & Career Recommendation Engine

An intelligent, explainable, and production-ready NLP application that parses resumes (PDF/DOCX/TXT), matches them contextually against Job Descriptions using **Sentence-BERT (`all-MiniLM-L6-v2`)**, computes calibrated multimodal fit scores, surfaces explainable AI reasoning, and recommends personalized career upskilling paths.

---

## 🌟 Core Features & Blueprint Alignment

1. **Document Ingestion & Multi-Format Parsing**:
   - **PDF & DOCX Extraction**: Built on PyMuPDF (`fitz`) and `python-docx` for robust multi-page extraction.
   - **Section Segmentation**: Automatically segments resume text into Header, Summary, Experience, Projects, Skills, and Education.
   - **Contact & Entity Extraction**: Uses regex and `spaCy` NER to extract names, emails, phone numbers, LinkedIn, and GitHub profiles.

2. **Semantic Matching with Sentence-BERT**:
   - Encodes job descriptions and resumes into dense 384-dimensional contextual vectors using `all-MiniLM-L6-v2`.
   - Overcomes vocabulary mismatch (e.g., matches "Deep Learning" with "Transformers", "K8s" with "Kubernetes", "Golang" with "Go").

3. **Multimodal Scoring Formula**:
   $$\ S = w_s S_{\text{semantic}} + w_k S_{\text{skills}} + w_e S_{\text{evidence}} \$$
   - $S_{\text{semantic}}$: Contextual cosine similarity between JD and resume.
   - $S_{\text{skills}}$: Weighted coverage of mandatory (80%) and preferred (20%) skills.
   - $S_{\text{evidence}}$: Alignment of years of experience, project depth, and granular sentence-level semantic matching.
   - Dynamic weight sliders with presets: *Balanced*, *Skill Heavy*, *Experience Heavy*.

4. **Explainable AI (XAI)**:
   - Automated executive natural language match rationale.
   - Color-coded badges for Matched Required Skills, Skill Gaps, Preferred Competencies, and Bonus Skills.
   - Multimodal Competency Radar Chart (Plotly).
   - Extracted project evidence snippets highlighting matching sentences and relevance percentages.

5. **Career Recommendation & Upskilling Engine**:
   - 3-Phase structured roadmap (Phase 1: Core Prerequisites, Phase 2: Applied Project, Phase 3: Differentiators).
   - Direct documentation and tutorial links for identified skill gaps.
   - Concrete, portfolio-grade project blueprints with target technologies and deliverables.

6. **Academic Benchmark (Sentence-BERT vs TF-IDF Baseline)**:
   - Rigorous empirical evaluation comparing S-BERT against TF-IDF n-gram baseline.
   - Evaluation Metrics: **NDCG@3**, **Precision@1**, **Precision@3**, **Mean Reciprocal Rank (MRR)**, **Spearman $\rho$**, **Pearson $r$**, and **Inference Latency**.
   - Lexical Gap & Synonym robustness comparison table and charts.

7. **Data Persistence**:
   - SQLite database (`data/hiresense.db`) storing past screening runs, job descriptions, and candidate rankings.

---

## 🚀 Running the Web Application

To run or restart the server manually:
```bash
streamlit run app.py
```

To run the automated test suite:
```bash
python test_pipeline.py
```

---

## 📁 Project Architecture

```
mini-proz/
├── app.py                      # Streamlit application UI & navigation
├── config.py                   # Configuration, paths, and default weights
├── test_pipeline.py            # End-to-end integration test suite
├── create_sample_docs.py       # Generator for sample PDF/DOCX resumes
├── requirements.txt            # Package dependencies
├── assets/
│   └── style.css               # Modern glassmorphism & typography CSS
├── modules/
│   ├── parser.py               # PyMuPDF, python-docx, spaCy text extraction
│   ├── taxonomy.py             # Comprehensive tech taxonomy & alias resolution
│   ├── semantic_matcher.py     # S-BERT embeddings & TF-IDF baseline
│   ├── scoring.py              # Multimodal scoring calculation
│   ├── explainable_ai.py       # XAI explanations, badges, radar data
│   ├── recommender.py          # Career pathways, resources, project blueprints
│   ├── database.py             # SQLite persistence layer
│   └── academic_eval.py        # Benchmark metrics (NDCG, MRR, Spearman)
└── data/
    ├── sample_jobs/            # Sample Job Descriptions (ML, FullStack, Data Science)
    ├── sample_resumes/         # Pre-built PDF, DOCX, and TXT resumes
    └── hiresense.db            # SQLite database
```
