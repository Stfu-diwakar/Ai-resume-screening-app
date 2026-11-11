# HireSense AI
### Semantic Resume Screening & Career Recommendation Engine

<p align="center">
  <strong>Turn resumes into meaningful hiring insights.</strong><br/>
  An explainable AI-powered platform for intelligent resume analysis, semantic job matching, candidate evaluation, and personalized career recommendations.
</p>

<p align="center">
  <a href="https://hiresense-ai-dwkr.netlify.app/"><strong>🌐 Visit HireSense AI Website</strong></a>
  &nbsp; • &nbsp;
  <a href="https://hiresenseai-dwkr.streamlit.app/"><strong>🚀 Launch AI Application</strong></a>
  &nbsp; • &nbsp;
  <a href="https://github.com/Stfu-diwakar/Ai-resume-screening-app"><strong>💻 Source Code</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/NLP-Sentence--BERT-68E4C5?style=for-the-badge" alt="Sentence-BERT"/>
  <img src="https://img.shields.io/badge/Explainable-AI-9BA8FF?style=for-the-badge" alt="Explainable AI"/>
</p>

---

## ✨ Overview

**HireSense AI** is an intelligent, explainable, NLP-powered resume screening and career recommendation platform. It parses resumes in PDF, DOCX, and TXT formats, compares candidate profiles with job descriptions using **Sentence-BERT (`all-MiniLM-L6-v2`)**, calculates structured fit scores, and explains the results through skill insights and evidence.

The platform is designed to make candidate evaluation more contextual and transparent while helping job seekers identify skill gaps and plan their next learning steps.

## 🔗 Live Demo

| Experience | Link |
|---|---|
| 🌐 **Project Website** | [hiresense-ai-dwkr.netlify.app](https://hiresense-ai-dwkr.netlify.app/) |
| 🚀 **Launch the AI Application** | [hiresenseai-dwkr.streamlit.app](https://hiresenseai-dwkr.streamlit.app/) |
| 💻 **GitHub Repository** | [Ai-resume-screening-app](https://github.com/Stfu-diwakar/Ai-resume-screening-app) |

> **Tip:** Visit the project website first, then select **Launch HireSense AI** to open the interactive screening application.

---

## 🌟 Key Features

### 1. Multi-Format Resume Parsing
- Extracts content from PDF, DOCX, and TXT resumes.
- Segments resumes into sections such as Summary, Experience, Projects, Skills, and Education.
- Uses regex and spaCy Named Entity Recognition (NER) to identify contact details and relevant entities.

### 2. Semantic Resume Matching
- Uses Sentence-BERT to create contextual 384-dimensional embeddings.
- Matches related concepts even when exact keywords differ.
- Recognizes contextual relationships such as **Deep Learning and Transformers**, or **K8s and Kubernetes**.
- Includes a TF-IDF baseline for comparison.

### 3. Explainable Candidate Scoring
The candidate fit score combines multiple signals:

\[
S = w_s S_{\text{semantic}} + w_k S_{\text{skills}} + w_e S_{\text{evidence}}
\]

- **Semantic score:** Contextual similarity between the resume and job description.
- **Skills score:** Weighted coverage of required and preferred skills.
- **Evidence score:** Relevance of experience, projects, and supporting resume statements.
- Supports configurable weights and scoring presets.

### 4. Explainable AI Insights
- Natural-language match rationale.
- Matched skills, missing skills, preferred competencies, and bonus skills.
- Competency radar visualizations.
- Relevant resume evidence snippets with matching context.

### 5. Career Recommendations
- Personalized skill-gap identification.
- A structured, three-phase learning roadmap.
- Learning resources and documentation links.
- Portfolio-oriented project ideas with suggested technologies and deliverables.

### 6. Model Evaluation & Benchmarking
Compares Sentence-BERT with a TF-IDF n-gram baseline using:
- NDCG@3
- Precision@1 and Precision@3
- Mean Reciprocal Rank (MRR)
- Spearman correlation
- Pearson correlation
- Inference latency

### 7. Screening History
- SQLite-backed storage for screening runs.
- Stores job descriptions and candidate ranking history.

---

## 🧰 Tech Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Application UI | Streamlit |
| NLP & Embeddings | Sentence-Transformers, Sentence-BERT |
| Text Processing | spaCy, Regex |
| Machine Learning | Scikit-learn, TF-IDF |
| Data Processing | NumPy, Pandas |
| Visualizations | Plotly |
| Document Parsing | PyMuPDF, python-docx |
| Database | SQLite |

---

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Stfu-diwakar/Ai-resume-screening-app.git
cd Ai-resume-screening-app
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
streamlit run app.py
```

Streamlit will display a local URL in your terminal, usually `http://localhost:8501`.

### 5. Run the test suite

```bash
python test_pipeline.py
```

---

## 📁 Project Structure

```text
Ai-resume-screening-app/
├── app.py
├── config.py
├── test_pipeline.py
├── create_sample_docs.py
├── requirements.txt
├── assets/
│   └── style.css
├── modules/
│   ├── parser.py
│   ├── taxonomy.py
│   ├── semantic_matcher.py
│   ├── scoring.py
│   ├── explainable_ai.py
│   ├── recommender.py
│   ├── database.py
│   └── academic_eval.py
└── data/
    ├── sample_jobs/
    ├── sample_resumes/
    └── hiresense.db
```

---

## 🔒 Privacy & Responsible Use

Resume files may contain personal information. Use candidate documents only with appropriate permission, protect access to screening history, and review AI-generated scores and recommendations rather than treating them as the sole basis for hiring decisions.

---

## 👨‍💻 Project

**HireSense AI — Semantic Resume Screening & Career Recommendation Engine**

Built with Python, NLP, machine learning, and Streamlit.

<p align="center">
  <a href="https://hiresense-ai-dwkr.netlify.app/"><strong>🌐 Explore HireSense AI</strong></a>
  &nbsp; • &nbsp;
  <a href="https://hiresenseai-dwkr.streamlit.app/"><strong>🚀 Try the Live Application</strong></a>
</p>
