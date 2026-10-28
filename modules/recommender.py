"""
Career Recommendation Engine
Analyzes skill gaps and generates tailored learning pathways,
portfolio project ideas, and learning resources.
"""
from typing import Any, Dict, List

# Curated repository of resources per skill/domain
SKILL_RESOURCE_CATALOG: Dict[str, Dict[str, Any]] = {
    "PyTorch": {
        "level": "Intermediate",
        "time": "3-4 weeks",
        "resources": [
            {"title": "Official PyTorch Tutorials", "url": "https://pytorch.org/tutorials/", "type": "Documentation"},
            {"title": "Deep Learning with PyTorch (fast.ai)", "url": "https://course.fast.ai/", "type": "Interactive Course"}
        ],
        "project": {
            "title": "Vision Transformer for Medical Image Classification",
            "desc": "Build and train a custom ViT in PyTorch with transfer learning, mixed precision, and Grad-CAM explainability."
        }
    },
    "TensorFlow": {
        "level": "Intermediate",
        "time": "3 weeks",
        "resources": [
            {"title": "TensorFlow Official Guides", "url": "https://www.tensorflow.org/tutorials", "type": "Documentation"},
            {"title": "DeepLearning.AI TensorFlow Developer", "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "type": "Specialization"}
        ],
        "project": {
            "title": "Production Time-Series Forecasting Pipeline",
            "desc": "Train an LSTM/GRU network with TF-Serving deployment and automated drift monitoring."
        }
    },
    "NLP": {
        "level": "Intermediate",
        "time": "4 weeks",
        "resources": [
            {"title": "Hugging Face NLP Course", "url": "https://huggingface.co/learn/nlp-course", "type": "Comprehensive Course"},
            {"title": "Stanford CS224N: Natural Language Processing", "url": "https://web.stanford.edu/class/cs224n/", "type": "University Course"}
        ],
        "project": {
            "title": "Multi-Document Semantic Summarizer & Entity Graph",
            "desc": "Fine-tune a T5 model for abstractive summarization combined with spaCy relation extraction."
        }
    },
    "RAG": {
        "level": "Advanced",
        "time": "2-3 weeks",
        "resources": [
            {"title": "LangChain Official RAG Tutorial", "url": "https://python.langchain.com/docs/use_cases/question_answering/", "type": "Tutorial"},
            {"title": "DeepLearning.AI: Building Systems with ChatGPT API", "url": "https://www.deeplearning.ai/", "type": "Course"}
        ],
        "project": {
            "title": "Enterprise Knowledge-Base Assistant with Hybrid Search",
            "desc": "Build a RAG system combining dense vector search (ChromaDB) with BM25 keyword filtering and reranking."
        }
    },
    "LLM": {
        "level": "Advanced",
        "time": "3 weeks",
        "resources": [
            {"title": "Large Language Model Course (GitHub)", "url": "https://github.com/mlabonne/llm-course", "type": "Open Source Guide"},
            {"title": "Hugging Face PEFT & LoRA Guide", "url": "https://huggingface.co/docs/peft", "type": "Documentation"}
        ],
        "project": {
            "title": "Domain-Specific Instruction Fine-Tuning using QLoRA",
            "desc": "Fine-tune a Llama-3 or Mistral 7B model on legal or financial contracts with evaluation benchmarking."
        }
    },
    "Docker": {
        "level": "Beginner / Intermediate",
        "time": "1-2 weeks",
        "resources": [
            {"title": "Docker Getting Started Guide", "url": "https://docs.docker.com/get-started/", "type": "Documentation"},
            {"title": "Docker for Beginners (freeCodeCamp)", "url": "https://www.freecodecamp.org/news/", "type": "Video Course"}
        ],
        "project": {
            "title": "Multi-Stage Dockerized ML Microservice",
            "desc": "Containerize a FastAPI model server with lightweight alpine multi-stage build and health check orchestration."
        }
    },
    "Kubernetes": {
        "level": "Intermediate / Advanced",
        "time": "3-4 weeks",
        "resources": [
            {"title": "Kubernetes Basics (kubernetes.io)", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "type": "Interactive Tutorial"},
            {"title": "Certified Kubernetes Administrator (CKA) Path", "url": "https://killercoda.com/playgrounds", "type": "Hands-on Lab"}
        ],
        "project": {
            "title": "Auto-Scaling Microservices on Minikube / K3s",
            "desc": "Deploy backend replicas with Horizontal Pod Autoscaler (HPA), Ingress routing, and Secrets management."
        }
    },
    "FastAPI": {
        "level": "Beginner / Intermediate",
        "time": "1-2 weeks",
        "resources": [
            {"title": "FastAPI Official Documentation", "url": "https://fastapi.tiangolo.com/", "type": "Documentation"},
            {"title": "Async Python and FastAPI Masterclass", "url": "https://testdriven.io/", "type": "Guide"}
        ],
        "project": {
            "title": "High-Throughput Asynchronous REST API with JWT & Celery",
            "desc": "Build an async API with Pydantic validation, background task queues, and automated OpenAPI documentation."
        }
    },
    "PostgreSQL": {
        "level": "Intermediate",
        "time": "2 weeks",
        "resources": [
            {"title": "PostgreSQL Official Tutorial", "url": "https://www.postgresql.org/docs/", "type": "Documentation"},
            {"title": "Use The Index, Luke! (SQL Performance)", "url": "https://use-the-index-luke.com/", "type": "Guide"}
        ],
        "project": {
            "title": "Database Schema Design & Query Optimizer Benchmark",
            "desc": "Design normalized relations with partitioning, composite indexes, and pgvector extension for similarity search."
        }
    },
    "React": {
        "level": "Intermediate",
        "time": "3 weeks",
        "resources": [
            {"title": "React Official Interactive Docs", "url": "https://react.dev/", "type": "Documentation"},
            {"title": "The Road to React (Robin Wieruch)", "url": "https://www.roadtoreact.com/", "type": "Book/Tutorial"}
        ],
        "project": {
            "title": "Modern Interactive Analytics Dashboard",
            "desc": "Build a responsive dashboard using React, Tailwind CSS, TypeScript, and TanStack Query."
        }
    },
    "AWS": {
        "level": "Intermediate",
        "time": "3-4 weeks",
        "resources": [
            {"title": "AWS Skill Builder Free Learning Plans", "url": "https://explore.skillbuilder.aws/", "type": "Official Training"},
            {"title": "AWS Solutions Architect Associate Guide", "url": "https://aws.amazon.com/certification/", "type": "Certification"}
        ],
        "project": {
            "title": "Serverless Event-Driven Data Pipeline",
            "desc": "Deploy AWS Lambda, S3 triggers, SQS queues, and DynamoDB using AWS SAM / CloudFormation."
        }
    },
    "CI/CD": {
        "level": "Beginner / Intermediate",
        "time": "1 week",
        "resources": [
            {"title": "GitHub Actions Documentation", "url": "https://docs.github.com/en/actions", "type": "Documentation"},
            {"title": "Continuous Delivery Pipeline Guide", "url": "https://martinfowler.com/articles/continuousIntegration.html", "type": "Architecture"}
        ],
        "project": {
            "title": "Automated Lint, Test, Build, and Deploy Workflow",
            "desc": "Create a GitHub Actions CI workflow that runs pytest, flake8, builds a Docker image, and deploys on tag push."
        }
    }
}

DEFAULT_GENERIC_RESOURCE = {
    "level": "Foundational",
    "time": "1-2 weeks",
    "resources": [
        {"title": "Official Technical Documentation & Cheat Sheets", "url": "https://devdocs.io/", "type": "Documentation"},
        {"title": "freeCodeCamp Interactive Library", "url": "https://www.freecodecamp.org/", "type": "Open Tutorials"}
    ],
    "project": {
        "title": "Hands-on Integration & Benchmark Project",
        "desc": "Build a modular application that demonstrates proficiency, clean testing, and GitHub documentation."
    }
}

def generate_recommendations(
    missing_required_skills: List[str],
    missing_preferred_skills: List[str],
    target_role: str = "Target Position"
) -> Dict[str, Any]:
    """
    Generate actionable career pathways, structured project ideas,
    and learning resources for identified skill gaps.
    """
    priority_1_skills = []
    priority_2_skills = []
    recommended_projects = []

    # Process Priority 1 (Required Gaps)
    for skill in missing_required_skills:
        info = SKILL_RESOURCE_CATALOG.get(skill, DEFAULT_GENERIC_RESOURCE)
        item = {
            "skill": skill,
            "priority": "Critical / Required",
            "priority_color": "#ef4444",
            "estimated_time": info["time"],
            "level": info["level"],
            "resources": info["resources"]
        }
        priority_1_skills.append(item)
        if "project" in info and info["project"]["title"] not in [p["title"] for p in recommended_projects]:
            recommended_projects.append({
                **info["project"],
                "target_skill": skill,
                "urgency": "High Priority"
            })

    # Process Priority 2 (Preferred Gaps)
    for skill in missing_preferred_skills:
        info = SKILL_RESOURCE_CATALOG.get(skill, DEFAULT_GENERIC_RESOURCE)
        item = {
            "skill": skill,
            "priority": "Competitive Advantage",
            "priority_color": "#f59e0b",
            "estimated_time": info["time"],
            "level": info["level"],
            "resources": info["resources"]
        }
        priority_2_skills.append(item)
        if len(recommended_projects) < 4 and "project" in info:
            if info["project"]["title"] not in [p["title"] for p in recommended_projects]:
                recommended_projects.append({
                    **info["project"],
                    "target_skill": skill,
                    "urgency": "Medium Priority"
                })

    # Fallback if no skills are missing (perfect candidate!)
    if not missing_required_skills and not missing_preferred_skills:
        recommended_projects.append({
            "title": f"Production-Grade End-to-End {target_role} Showcase",
            "desc": "Design and publish a distributed system architecture repository demonstrating high scalability, observability, and unit test coverage.",
            "target_skill": "Advanced Architecture",
            "urgency": "Portfolio Polish"
        })

    return {
        "target_role": target_role,
        "total_gaps_count": len(missing_required_skills) + len(missing_preferred_skills),
        "priority_1_gaps": priority_1_skills,
        "priority_2_gaps": priority_2_skills,
        "recommended_projects": recommended_projects[:5],
        "learning_roadmap_stages": [
            {
                "stage": "Phase 1: Core Prerequisites (Weeks 1-2)",
                "focus": [s["skill"] for s in priority_1_skills[:2]] if priority_1_skills else ["Core Frameworks"],
                "goal": "Bridge mandatory gaps required for baseline qualification."
            },
            {
                "stage": "Phase 2: Project Implementation (Weeks 3-4)",
                "focus": [recommended_projects[0]["title"]] if recommended_projects else ["Applied Project"],
                "goal": "Build an open-source project to demonstrate practical mastery."
            },
            {
                "stage": "Phase 3: Differentiators & Polish (Weeks 5-6)",
                "focus": [s["skill"] for s in priority_2_skills[:2]] if priority_2_skills else ["Cloud & Architecture"],
                "goal": "Acquire competitive edge competencies and optimize portfolio presentation."
            }
        ]
    }
