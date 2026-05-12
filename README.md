# Production RAG System for IT and Security Triage

A portfolio-ready AI system that uses retrieval-augmented generation to triage IT support tickets and security alerts using internal documentation.

## Purpose

This project demonstrates production-oriented AI engineering skills, including document retrieval, embeddings, ticket classification, severity scoring, FastAPI development, evaluation metrics, testing, Docker, and cloud-ready deployment.

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
- Linting and formatting with Ruff

## Current Milestones

- [ ] Project structure and housekeeping
- [ ] Local document ingestion
- [ ] Text chunking
- [ ] Embedding generation
- [ ] Vector search with FAISS
- [ ] Ticket classification
- [ ] Severity scoring
- [ ] FastAPI triage endpoint
- [ ] Evaluation metrics
- [ ] Streamlit dashboard
- [ ] Docker deployment