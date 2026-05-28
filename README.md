# Production RAG System for IT and Security Triage

![CI](https://github.com/tasn78/production-rag-it-security-triage/actions/workflows/ci.yml/badge.svg)

A production-oriented AI backend system that uses retrieval-augmented generation concepts to triage IT support tickets and security alerts using internal documentation.

The system classifies tickets, calculates severity, retrieves relevant knowledge-base evidence, tracks requests with unique request IDs, captures human feedback, and exposes the workflow through FastAPI and a Streamlit dashboard.

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
- Streamlit dashboard development
- Request history logging with request ID tracing
- Human feedback capture for triage evaluation
- Feedback summary metrics
- Docker Compose multi-service execution

## Current Status

The project currently supports an end-to-end local triage and feedback workflow:

```text
Ticket or alert text
    ↓
FastAPI triage request
    ↓
Unique request_id generation
    ↓
Rule-based classification
    ↓
Severity scoring
    ↓
Knowledge-base retrieval
    ↓
Structured API response
    ↓
Streamlit dashboard display
    ↓
Human feedback capture
    ↓
Request and feedback logs
    ↓
Feedback summary metrics

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
- [x] Streamlit dashboard
- [x] Docker Compose support for FastAPI and Streamlit
- [x] Request logging with local JSONL persistence
- [x] Request ID tracking across triage, history, and feedback
- [x] Feedback capture for human review
- [x] Feedback summary metrics
- [x] API health status display in dashboard
- [x] Streamlit dashboard history view
- [x] Downloadable triage reports

## Planned Features
- [ ] Optional LLM-generated triage summaries
- [ ] Cloud deployment
- [ ] Expanded evaluation dataset
- [ ] More polished dashboard styling and screenshots
- [ ] Authentication or role-based access control

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
│   ├── feedback_logger.py      # JSONL feedback logging and feedback summaries
│   ├── request_logger.py       # JSONL request history logging
│   ├── schemas.py              # Shared triage domain types
│   ├── service.py              # Triage workflow orchestration
│   └── severity.py             # Explainable severity scoring
└── main.py                     # FastAPI application entry point

frontend/
└── streamlit_app.py            # Streamlit triage dashboard
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
- Request history endpoint
- Feedback submission endpoint
- Feedback summary endpoint
- Request ID tracking

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
  "request_id": "30094c91-f1b3-4b33-875b-76053410fd1d",
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
      "text": "Example retrieved evidence text.",
      "score": 0.7079,
      "rank": 1
    }
  ]
}
```
## API Endpoints

```text
GET  /health
POST /triage
GET  /triage/history
POST /triage/feedback
GET  /triage/feedback/summary
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

## Run with Docker Compose

Build and start the FastAPI backend and Streamlit dashboard:

```powershell
docker compose up --build

## GitHub Actions CI

This repository includes a GitHub Actions workflow that runs on pushes and pull requests to `main`.

The CI workflow runs:

```text
ruff check .
ruff format --check .
pytest
```

This helps verify that code remains linted, formatted, and tested before changes are merged or shared.


## Streamlit Dashboard

The Streamlit dashboard provides an interactive interface for the triage workflow.

Dashboard features include:

- Ticket or alert text input
- Configurable number of retrieved evidence chunks
- Triage category, severity, and severity score display
- Matched keywords and severity reasons
- Retrieved knowledge-base evidence
- Human feedback form
- Feedback summary metrics
- Recent feedback table
- Recent triage history table
- API health/status display
- Downloadable Markdown triage reports

After starting Docker Compose, open:

http://127.0.0.1:8501
```

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