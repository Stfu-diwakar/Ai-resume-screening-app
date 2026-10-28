"""
Skill Taxonomy and Entity Normalization Engine
"""
import re
from typing import Dict, List, Set, Tuple

# Comprehensive taxonomy organized by domain
SKILL_TAXONOMY: Dict[str, List[str]] = {
    "AI / Machine Learning": [
        "Machine Learning", "Deep Learning", "Natural Language Processing", "NLP",
        "Computer Vision", "Transformers", "BERT", "GPT", "LLM", "Large Language Models",
        "RAG", "Retrieval Augmented Generation", "LangChain", "LlamaIndex", "Hugging Face",
        "PyTorch", "TensorFlow", "Keras", "Scikit-Learn", "XGBoost", "LightGBM",
        "Data Science", "Feature Engineering", "Model Evaluation", "Fine-tuning",
        "Prompt Engineering", "Reinforcement Learning", "Vector Embeddings", "Semantic Search"
    ],
    "Programming Languages": [
        "Python", "Java", "C++", "C", "C#", "Go", "Rust", "JavaScript", "TypeScript",
        "R", "Scala", "Kotlin", "Swift", "PHP", "Ruby", "SQL", "Bash", "Shell", "HTML", "CSS"
    ],
    "Frameworks & Backend": [
        "FastAPI", "Flask", "Django", "Node.js", "Express.js", "Spring Boot", "ASP.NET",
        "REST API", "GraphQL", "gRPC", "Microservices", "Celery", "Kafka", "RabbitMQ", "Redis"
    ],
    "Frontend & UI": [
        "React", "Next.js", "Vue.js", "Angular", "Tailwind CSS", "Bootstrap",
        "Redux", "HTML5", "CSS3", "Streamlit", "Gradio", "Webpack", "Vite"
    ],
    "Data Engineering & Databases": [
        "PostgreSQL", "MySQL", "MongoDB", "SQLite", "Cassandra", "DynamoDB",
        "Snowflake", "BigQuery", "Apache Spark", "Airflow", "ETL", "Data Pipelines",
        "Elasticsearch", "Pinecone", "ChromaDB", "Milvus", "Weaviate", "Pandas", "NumPy"
    ],
    "Cloud & DevOps": [
        "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker",
        "Kubernetes", "Terraform", "CI/CD", "GitHub Actions", "GitLab CI", "Jenkins",
        "Linux", "Nginx", "Kubeflow", "MLflow", "Serverless", "Monitoring", "Prometheus"
    ],
    "Software Engineering & Tools": [
        "Git", "GitHub", "GitLab", "Unit Testing", "Pytest", "TDD", "System Design",
        "Object Oriented Programming", "OOP", "Design Patterns", "Agile", "Scrum",
        "Jira", "Clean Architecture", "Code Review"
    ],
    "Soft Skills & Core Competencies": [
        "Problem Solving", "Communication", "Leadership", "Teamwork", "Analytical Thinking",
        "Mentorship", "Collaboration", "Project Management", "Critical Thinking"
    ]
}

# Skill synonyms / aliases mapped to canonical name
SKILL_ALIASES: Dict[str, str] = {
    "golang": "Go",
    "k8s": "Kubernetes",
    "py": "Python",
    "js": "JavaScript",
    "ts": "TypeScript",
    "reactjs": "React",
    "react.js": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "angularjs": "Angular",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "tf": "TensorFlow",
    "sklearn": "Scikit-Learn",
    "scikit-learn": "Scikit-Learn",
    "scikit learn": "Scikit-Learn",
    "huggingface": "Hugging Face",
    "hf": "Hugging Face",
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud platform": "GCP",
    "azure": "Azure",
    "rest": "REST API",
    "restful": "REST API",
    "rest api": "REST API",
    "rest apis": "REST API",
    "microservice": "Microservices",
    "microservices": "Microservices",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "llm": "LLM",
    "llms": "LLM",
    "large language models": "LLM",
    "rag": "RAG",
    "retrieval-augmented generation": "RAG",
    "retrieval augmented generation": "RAG",
    "vector database": "Vector Embeddings",
    "vector databases": "Vector Embeddings",
    "ci cd": "CI/CD",
    "ci/cd": "CI/CD",
    "mlflow": "MLflow",
    "spark": "Apache Spark",
    "pyspark": "Apache Spark",
    "airflow": "Airflow",
    "oop": "OOP",
    "object oriented programming": "OOP",
    "tdd": "TDD",
    "test driven development": "TDD"
}

def get_canonical_skill(skill_name: str) -> str:
    """Return the canonical representation of a skill or alias."""
    clean = skill_name.strip()
    lower = clean.lower()
    if lower in SKILL_ALIASES:
        return SKILL_ALIASES[lower]
    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            if skill.lower() == lower:
                return skill
    return clean

def extract_skills(text: str) -> Dict[str, List[str]]:
    """
    Extract skills from text by matching against taxonomy and alias dictionary.
    Returns:
        dict: {
            "all_skills": [unique canonical skill names],
            "by_category": {category_name: [skills_found]},
            "skill_counts": {canonical_name: occurrence_count}
        }
    """
    if not text:
        return {"all_skills": [], "by_category": {}, "skill_counts": {}}

    found_skills: Set[str] = set()
    skill_counts: Dict[str, int] = {}
    by_category: Dict[str, List[str]] = {cat: [] for cat in SKILL_TAXONOMY}

    text_lower = f" {text.lower()} "

    # 1. Match taxonomy skills
    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            pattern = r'(?<![a-zA-Z0-9_#+])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9_#+])'
            matches = list(re.finditer(pattern, text_lower))
            if matches:
                canonical = get_canonical_skill(skill)
                found_skills.add(canonical)
                skill_counts[canonical] = skill_counts.get(canonical, 0) + len(matches)
                if canonical not in by_category[category]:
                    by_category[category].append(canonical)

    # 2. Match aliases
    for alias, canonical in SKILL_ALIASES.items():
        pattern = r'(?<![a-zA-Z0-9_#+])' + re.escape(alias.lower()) + r'(?![a-zA-Z0-9_#+])'
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            found_skills.add(canonical)
            skill_counts[canonical] = skill_counts.get(canonical, 0) + len(matches)
            # Find category for canonical
            for cat, skl_list in SKILL_TAXONOMY.items():
                if any(s.lower() == canonical.lower() for s in skl_list):
                    if canonical not in by_category[cat]:
                        by_category[cat].append(canonical)
                    break

    # Clean empty categories
    by_category = {k: v for k, v in by_category.items() if len(v) > 0}

    return {
        "all_skills": sorted(list(found_skills)),
        "by_category": by_category,
        "skill_counts": skill_counts
    }
