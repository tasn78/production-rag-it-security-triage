# Production RAG System for IT and Security Triage

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

## Evaluation

The project includes a labeled JSONL evaluation set and a local evaluation script.

Run evaluation:

```powershell
python -m scripts.run_evaluation