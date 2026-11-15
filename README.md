# HireSense AI — Intelligent Resume Screening & Applicant Tracking System

HireSense AI is an explainable AI-assisted recruitment workspace built with Python and Streamlit. It combines resume parsing, contextual resume-to-job matching, candidate ranking, recruiter filters, a persistent hiring pipeline, and skill-gap insights in one application.

**The goal:** help small companies and startups organize high-volume applications and make candidate review faster and more consistent. HireSense is decision-support software; it does not make hiring decisions or automatically reject candidates.

<p align="center">
  <a href="https://hiresense-ai-dwkr.netlify.app/"><strong>Project Website</strong></a> ·
  <a href="https://hiresenseai-dwkr.streamlit.app/"><strong>Launch Application</strong></a> ·
  <a href="https://github.com/Stfu-diwakar/Ai-resume-screening-app"><strong>Source Code</strong></a>
</p>

<p align="center">
  ![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
  ![Streamlit](https://img.shields.io/badge/Streamlit-Application-FF4B4B?logo=streamlit&logoColor=white)
  ![NLP](https://img.shields.io/badge/NLP-Sentence--BERT-6558D3)
  ![Database](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
</p>

---

## Contents

- [Product overview](#product-overview)
- [Features](#features)
- [Recruiter workflow](#recruiter-workflow)
- [Matching methodology](#matching-methodology)
- [Technology stack](#technology-stack)
- [Project structure](#project-structure)
- [Local setup](#local-setup)
- [Sample data and testing](#sample-data-and-testing)
- [Configuration and deployment](#configuration-and-deployment)
- [Limitations and responsible use](#limitations-and-responsible-use)
- [Roadmap](#roadmap)
- [Developer](#developer)

## Product overview

Small hiring teams often receive many applications for a single opening. Reviewing every document manually, extracting qualifications, comparing candidates, and tracking interview stages can become repetitive and inconsistent.

HireSense AI brings these activities into a structured workspace:

1. Import resumes and extract candidate information.
2. Create and save job descriptions.
3. Compare candidate profiles against role requirements.
4. Rank and filter applicants using explainable signals.
5. Track candidates through the hiring pipeline.
6. Compare profiles and export candidate records.

The application also retains the original candidate-inspection, career recommendation, screening-history, and academic benchmarking workspaces.

## Features

### Recruiter ATS workspace

**Bulk resume intake**
- Upload multiple PDF and DOCX resumes in one operation.
- Parse documents into candidate profiles using the existing parser.
- Extract candidate name, email, phone, skills, experience, education sections, and available profile links.
- Detect repeated uploads using SHA-256 file fingerprints.
- Report unreadable files and individual parsing errors without stopping the entire batch.
- Identify scanned/image-only PDFs that require OCR before their text can be extracted.

**Job description management**
- Create and save multiple job descriptions.
- Keep separate candidate cohorts and rankings for different roles.
- Extract required skills, preferred skills, and experience requirements through the existing JD parser.

**Candidate ranking and filtering**
- Rank candidate profiles against the selected job.
- Display a match score and its component breakdown.
- Filter by minimum match score, pipeline stage, skills, location, years of experience, 10th percentage, 12th percentage, CGPA, and graduation-year range.
- Review matched skills and missing required/preferred skills.
- Inspect candidate details before updating their hiring stage.

Academic values are extracted only when recognizable labels and values are present. Missing values remain blank instead of being fabricated.

**Hiring pipeline**

Candidates can be moved through:

`Applied → Shortlisted → Interview → Offer / Rejected`

Stage changes are stored in SQLite and timestamped in an activity table.

**Candidate comparison and export**
- Compare two or three candidate profiles side by side.
- Export the candidate database to CSV.
- Identify email addresses belonging to shortlisted candidates for recruiter communication.

### AI-powered resume analysis

**Contextual matching**
- Sentence-BERT embeddings using `all-MiniLM-L6-v2`.
- TF-IDF fallback when the embedding model cannot be loaded.
- Skill coverage and experience alignment.
- Explainable match components rather than an unexplained single score.

**Skill-gap insights**
- Matched mandatory and preferred skills.
- Missing required competencies.
- Career learning roadmaps and suggested portfolio projects in the Career Plan workspace.

**Duplicate detection**
- SHA-256 fingerprints prevent identical resume files from being imported repeatedly.
- Different files containing the same person's information are not guaranteed to be identified as duplicates.

### Existing analytical workspaces

- **Screening:** Guided resume screening, job description selection, semantic ranking, and explanations.
- **Candidate Inspector:** Detailed inspection of screening results.
- **Career Plan:** Personalized skill-gap analysis and learning recommendations.
- **Academic Benchmark:** Sentence-BERT versus TF-IDF evaluation, ranking metrics, and synonym tests.
- **Screening History:** SQLite-backed records of previous screening runs.
- **Recruiter ATS:** Persistent applicant profiles, filters, job management, pipeline, comparison, and CSV export.

## Recruiter workflow

1. Open the **Recruiter ATS** workspace.
2. Visit **Jobs** and create a role with its full job description.
3. Open **Import resumes** and upload a batch of PDF/DOCX files.
4. Open **Overview & ranking** and select the target role.
5. Adjust filters to narrow the candidate list.
6. Inspect match explanations and candidate evidence.
7. Move suitable candidates to Shortlisted, Interview, Offer, or Rejected.
8. Use **Compare & export** to compare profiles or download the candidate database.

## Matching methodology

The original screening engine combines semantic similarity, skill coverage, and supporting evidence:

[
S = w_s S_{semantic} + w_k S_{skills} + w_e S_{evidence}
]

The original screening workspace exposes configurable weights.

The recruiter ATS ranking uses the following default weighting:

| Component | Weight | What it measures |
|---|---:|---|
| Semantic similarity | 35% | Contextual similarity between the role description and resume |
| Skill coverage | 50% | Coverage of required and preferred skills |
| Experience alignment | 15% | Candidate experience relative to the role requirement |

The ATS score is a ranking aid, not a probability of being hired or a measure of a person's overall ability. Missing academic information should be reviewed manually; it should not be interpreted as a zero score.

## Technology stack

| Area | Technology |
|---|---|
| Language | Python 3.10+ |
| User interface | Streamlit |
| Semantic NLP | Sentence-Transformers, Sentence-BERT |
| Lexical baseline | Scikit-learn TF-IDF |
| Document parsing | PyMuPDF, python-docx |
| NLP utilities | spaCy, regular expressions |
| Data processing | Pandas, NumPy |
| Visualization | Plotly |
| Persistence | SQLite |
| Export | CSV |

## Project structure

```text
Ai-resume-screening-app/
├── app.py
├── config.py
├── requirements.txt
├── test_pipeline.py
├── create_sample_docs.py
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
│   ├── academic_eval.py
│   └── recruiter_workspace.py
└── data/
    ├── sample_jobs/
    ├── sample_resumes/
    └── hiresense.db
```

The ATS tables are initialized in the existing SQLite database. Candidate profile records and pipeline stages are stored locally in that database.

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/Stfu-diwakar/Ai-resume-screening-app.git
cd Ai-resume-screening-app
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The first Sentence-Transformers run may download the embedding model. If model loading is unavailable, matching falls back to TF-IDF.

### 4. Launch HireSense AI

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

`http://localhost:8501`

### 5. Run the existing screening tests

```bash
python test_pipeline.py
```

## Sample data and testing

The repository includes five synthetic candidate profiles in PDF/DOCX/TXT formats and sample job descriptions for Full Stack Engineer, Senior ML Engineer, Python Developer, Business Analyst, and Project Manager. In the Recruiter ATS workspace, use **Load included demo resume dataset** and **Import included sample job descriptions** to populate a demo hiring workspace. The app deduplicates identical resume files by fingerprint; only one format per sample candidate is imported by the demo loader.

Suggested manual acceptance checks:

| Test | Expected result |
|---|---|
| Upload several valid PDF/DOCX resumes | Each readable file becomes a candidate profile |
| Upload the same file again | Duplicate is skipped |
| Upload an unreadable or image-only PDF | A clear per-file warning is shown |
| Save multiple job descriptions | Roles remain available after app reruns |
| Change the active role | Candidate ranking is recalculated for that role |
| Apply skill/location/experience filters | Only matching profiles remain visible |
| Apply academic filters | Profiles with missing values are not treated as qualified |
| Change a candidate's stage | The new stage persists after refresh |
| Compare candidates | Selected profiles appear in a comparison table |
| Export candidates | A CSV file downloads with profile and pipeline fields |

For realistic testing, use consented or synthetic resumes and include a variety of experience levels, education formats, skill synonyms, missing fields, and duplicate files.

## Configuration and deployment

- Application settings and database paths are defined in `config.py`.
- The database is SQLite and is suitable for local demonstrations and small single-instance deployments.
- Streamlit Community Cloud or another Streamlit-compatible host can run the application when dependencies and persistent storage are configured.
- A local SQLite file on an ephemeral hosting filesystem may be reset during redeployment or instance replacement. Use a persistent disk or migrate to a managed database for production.
- Do not commit real candidate resumes, personal information, API keys, or production database files to a public repository.

## Limitations and responsible use

HireSense AI is a prototype and demonstration ATS, not a production HR compliance platform.

- Scanned PDFs need OCR; text extraction alone cannot reliably parse image-only documents.
- Academic extraction is heuristic and depends on recognizable labels and formatting. Recruiters should verify extracted values against the original document.
- Resume parsing can miss or misclassify fields when layouts are complex.
- File-hash duplicate detection catches identical files, not every resume belonging to the same person.
- Bulk email sending is not implemented. The workspace surfaces shortlisted email addresses for copying into an approved email client; no messages are sent automatically.
- SQLite is intended for local/small-scale use. Multi-user concurrency, authentication, authorization, and production-grade audit controls require additional infrastructure.
- Candidate information is sensitive personal data. Obtain appropriate consent, restrict access, define retention periods, and delete records when no longer needed.
- Do not use protected characteristics or proxy variables to rank applicants.
- AI scores can contain errors and bias. Keep a human reviewer in the loop and never use a score as the sole basis for rejection or selection.

## Roadmap

Potential next steps for a production-oriented release:

- Authentication, recruiter roles, and organization-level access controls.
- OCR for scanned resumes and improved structured education parsing.
- Candidate-level duplicate detection using normalized contact details and similarity checks.
- Interview scheduling, feedback forms, and configurable pipeline stages.
- Email provider integration with consent, templates, rate limits, and delivery logs.
- PostgreSQL support, background parsing jobs, and cloud object storage.
- Automated regression tests for parsers, scoring, filters, and pipeline transitions.
- Data retention controls and candidate data deletion/export workflows.

## Developer

**Diwakar Jha**  
MCA — Artificial Intelligence & Machine Learning, Chandigarh University

- [LinkedIn](https://www.linkedin.com/in/diwakar-jha-064130229/)
- [GitHub](https://github.com/Stfu-diwakar)
- [HireSense AI repository](https://github.com/Stfu-diwakar/Ai-resume-screening-app)

---

<p align="center"><strong>HireSense AI — Better screening. Clearer decisions. More structured hiring.</strong></p>
