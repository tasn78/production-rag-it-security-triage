# Production RAG System for IT and Security Triage

![CI](https://github.com/tasn78/production-rag-it-security-triage/actions/workflows/ci.yml/badge.svg)

A production-oriented AI backend system that uses retrieval-augmented generation concepts to triage IT support tickets and security alerts using internal documentation.

The system classifies tickets, calculates severity, retrieves relevant knowledge-base evidence, and exposes the workflow through a FastAPI endpoint.

## Purpose

This project demonstrates practical AI engineering and backend software development skills, including:

- Document ingestion and chunking
- Embedding generation with SentenceTransformers
- Vector search with FAISS
- Rule-based ticket classification
- Explainable severity scoring
- FastAPI backend development
- Structured API responses
- Unit testing with pytest
- Ruff linting and formatting
- Docker-based backend execution
- GitHub Actions CI
- Git/GitHub version control
- Production-oriented project organization

## Current Status

The project currently supports an end-to-end local triage workflow:

```text
Ticket or alert text
    ↓
Rule-based classification
    ↓
Severity scoring
    ↓
Knowledge-base retrieval
    ↓
Structured FastAPI response
```

Example input:

```text
Nginx logs show repeated 401 and 429 responses from the same external IP.
```

Example output:

```text
Category: Security Alert
Severity: High
Evidence: nginx_security.md
```

## Features Completed

- [x] Project structure and housekeeping
- [x] Local document ingestion
- [x] Text chunking with overlap
- [x] Sample IT/security knowledge-base documents
- [x] Embedding generation
- [x] Vector search with FAISS
- [x] End-to-end retriever
- [x] Ticket classification
- [x] Severity scoring
- [x] Triage service orchestration
- [x] FastAPI triage endpoint
- [x] Manual retrieval demo script
- [x] Manual API demo script
- [x] Evaluation metrics
- [x] Unit tests for core backend logic
- [x] Ruff linting and formatting
- [x] Docker support for the FastAPI backend
- [x] GitHub Actions CI

## Planned Features

- [ ] Streamlit dashboard
- [ ] Saved triage records and request logging
- [ ] Feedback capture for human review
- [ ] Optional LLM-generated triage summaries
- [ ] Cloud deployment
- [ ] Expanded evaluation dataset

## Engineering Standards

This project follows production-oriented Python software practices:

- Descriptive module, class, function, and variable names
- Type hints for function signatures
- Google-style docstrings for public modules, classes, and functions
- Clear separation between API routes, business logic, RAG logic, and evaluation logic
- Unit tests for core logic
- Explicit input validation and error handling
- No hardcoded secrets or credentials
- Local artifacts, virtual environments, logs, and secrets excluded from Git
- Deterministic baseline logic before adding LLM behavior
- Automated linting, formatting, and tests through GitHub Actions CI

## Architecture

```text
app/
├── api/
│   └── routes_triage.py        # FastAPI triage route
├── evaluation/
│   ├── evaluation_schemas.py   # Evaluation data structures
│   └── evaluator.py            # Evaluation metric calculations
├── rag/
│   ├── chunking.py             # Text normalization and chunking
│   ├── document_loader.py      # Local document loading
│   ├── embeddings.py           # SentenceTransformer embedding wrapper
│   ├── knowledge_base.py       # Document-to-chunk preparation
│   ├── retriever.py            # End-to-end knowledge-base retriever
│   └── vector_store.py         # FAISS vector search
├── triage/
│   ├── classifier.py           # Rule-based ticket classification
│   ├── schemas.py              # Shared triage domain types
│   ├── service.py              # Triage workflow orchestration
│   └── severity.py             # Explainable severity scoring
└── main.py                     # FastAPI application entry point
```

## Knowledge Base Documents

Sample documents are stored in:

```text
data/docs/
```

Current sample documents include:

- `nginx_security.md`
- `password_reset.md`
- `shared_drive_access.md`
- `vpn_troubleshooting.md`

These documents simulate internal IT/security knowledge-base content used for retrieval.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run Tests

```powershell
pytest
```

At the current milestone, the test suite covers:

- Text chunking
- Document loading
- Knowledge-base preparation
- Embedding validation
- FAISS vector search
- Retrieval workflow
- Ticket classification
- Severity scoring
- Triage service orchestration
- FastAPI triage endpoint
- Evaluation utilities

## Code Quality Checks

Run Ruff linting:

```powershell
ruff check .
```

Run Ruff formatting check:

```powershell
ruff format --check .
```

Apply Ruff formatting:

```powershell
ruff format .
```

Recommended local quality check before committing:

```powershell
ruff check .
ruff format --check .
pytest
```

## Evaluation

The project includes a labeled JSONL evaluation set and a local evaluation script.

Run evaluation:

```powershell
python -m scripts.run_evaluation
```

Current baseline results:

```text
category_accuracy: 100.00%
severity_accuracy: 100.00%
retrieval_hit_at_k: 100.00%
top_source_accuracy: 100.00%
```

Evaluation currently measures:

- Category classification accuracy
- Severity scoring accuracy
- Retrieval hit@k
- Top retrieved source accuracy

The evaluation dataset is intentionally small at this stage and is designed to verify the current baseline workflow. Future work will expand the evaluation set with more realistic ticket variations and edge cases.

## Run the Retrieval Demo

```powershell
python -m scripts.demo_retrieval
```

This script loads the sample knowledge-base documents, builds a local FAISS index, and retrieves relevant chunks for example IT/security queries.

## Run the FastAPI Server Locally

```powershell
uvicorn app.main:app --reload
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

Triage endpoint:

```text
POST /triage
```

## Example API Request

```json
{
  "ticket_text": "Nginx logs show repeated 401 and 429 responses from the same external IP.",
  "top_k": 3
}
```

## Example API Response

```json
{
  "ticket_text": "Nginx logs show repeated 401 and 429 responses from the same external IP.",
  "category": "Security Alert",
  "matched_keywords": ["external ip"],
  "severity": "High",
  "severity_score": 7,
  "severity_reasons": [
    "Base severity score applied.",
    "Security alert category increases severity.",
    "High-risk security indicators detected: external ip"
  ],
  "retrieved_evidence": [
    {
      "source_name": "nginx_security.md",
      "chunk_index": 0,
      "score": 0.7079,
      "rank": 1
    }
  ]
}
```

## Run the API Demo Script

Start the FastAPI server first:

```powershell
uvicorn app.main:app --reload
```

Then open a second terminal and run:

```powershell
python -m scripts.demo_api_request
```

The script sends example triage requests to the local API and prints category, severity, severity reasons, and retrieved evidence.

## Run with Docker

Build and start the FastAPI backend:

```powershell
docker compose up --build
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Stop the running container with `Ctrl + C`, then remove the container and network:

```powershell
docker compose down
```

## GitHub Actions CI

This repository includes a GitHub Actions workflow that runs on pushes and pull requests to `main`.

The CI workflow runs:

```text
ruff check .
ruff format --check .
pytest
```

This helps verify that code remains linted, formatted, and tested before changes are merged or shared.

## Example Demo Results

```text
Ticket: Nginx logs show repeated 401 and 429 responses from the same external IP.
Category: Security Alert
Severity: High
Retrieved Evidence:
  Rank 1 | nginx_security.md | Chunk 0
  Rank 2 | nginx_security.md | Chunk 1
  Rank 3 | nginx_security.md | Chunk 2
```

```text
Ticket: User connects to VPN but cannot access internal resources.
Category: VPN / Network Access
Severity: Low
Retrieved Evidence:
  Rank 1 | vpn_troubleshooting.md | Chunk 0
  Rank 2 | vpn_troubleshooting.md | Chunk 1
  Rank 3 | shared_drive_access.md | Chunk 0
```

```text
Ticket: User cannot access shared drive after password reset.
Category: Shared Drive / File Access
Severity: Low
Retrieved Evidence:
  Rank 1 | shared_drive_access.md | Chunk 0
  Rank 2 | password_reset.md | Chunk 0
  Rank 3 | shared_drive_access.md | Chunk 1
```

## Why This Project Matters

Many organizations receive repetitive IT tickets and security alerts that require fast, consistent triage. This project shows how retrieval, classification, severity scoring, and backend API design can be combined into a practical AI-assisted workflow.

The system is intentionally built with deterministic baseline logic first. This makes the workflow explainable, testable, and auditable before adding optional LLM-generated summaries or more advanced automation.