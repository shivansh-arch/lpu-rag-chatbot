# LPU RAG Chatbot

A Retrieval-Augmented Generation (RAG) assistant for LPU students. Answers natural-language questions about university announcements, placement/internship drives, and personal academic data (attendance, CGPA, fee status, messages) — pulling from both a shared institutional knowledge base and live per-student data.

## Problem Statement

LPU students receive academic and career-critical information — results, notices, placement/internship drive announcements, circulars — scattered across disconnected UMS/LPU Touch modules with no unified way to query it. Students often miss deadlines or eligibility windows because there's no single place to ask "what's relevant to me right now."

This project builds a RAG-based assistant that lets a student ask questions like *"Am I eligible for the Amazon drive?"* or *"What messages do I have?"* and get a grounded, accurate answer — instead of manually checking every tab.

## Architecture

The system is built on **two separate data paths**, kept deliberately isolated:

```
                         ┌─────────────────────┐
                         │     Student asks     │
                         │      a question       │
                         └──────────┬───────────┘
                                    │
                            pipeline.py (orchestrator)
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                                             │
     Path A: Institutional KB                    Path B: Live Student Data
   (shared, same for all students)              (private, one student at a time)
              │                                             │
      retrieval.py                                  student_fetch.py
   (semantic search over                          (HTTP calls to the
    vector DB of notices)                          student data API)
              │                                             │
        ChromaDB                                    mock_student_api
   (embedded via a local                           (stands in for real
   sentence-transformers                            UMS; returns raw
        model)                                       per-student facts)
              │                                             │
              └─────────────────────┬─────────────────────┘
                                    │
                        Gemini (with function-calling tools)
                     Combines the retrieved policy text with
                    on-demand calls to per-student data tools,
                        and generates a grounded answer
```

**Why two paths?** Institutional facts (placement cutoffs, exam policy) are the same for every student and safe to bulk-index into a searchable knowledge base. Personal facts (a student's own attendance, CGPA, messages) are private and must be fetched live, per request, for the one student asking — never bulk-stored. Keeping these architecturally separate avoids ever holding another student's private data in the same place as public institutional content.

**How routing works:** Path A retrieval runs on every question (it's cheap and general-purpose — semantic search naturally handles any topic in the corpus). Path B access is handled through **Gemini's function calling**: the model is given four tools (`get_attendance`, `get_cgpa`, `get_fee_status`, `get_messages`), each pre-bound to the logged-in student's ID via a closure, so the model can choose *which* tools it needs per question but can never choose *whose* data it fetches.

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python |
| Mock student data API | FastAPI + Pydantic |
| Vector database | ChromaDB (local, persistent) |
| Embedding model | `sentence-transformers` (`all-MiniLM-L6-v2`), run locally |
| LLM | Gemini (`gemini-3.7-flash`) via the `google-genai` SDK, using automatic function calling |
| HTTP client (Path B) | `requests` |

## Project Structure

```
lpu-rag-chatbot/
├── mock_student_api/       # Stand-in for real UMS — swapped out later, not the bot itself
│   ├── data.py               # Fake per-student dataset
│   ├── models.py             # Pydantic response schemas
│   └── main.py                # FastAPI app; raw-data endpoints only
├── rag_bot/                 # The actual product
│   ├── config.py               # API keys, base URLs
│   ├── ingest.py                # Embeds and stores announcements in ChromaDB
│   ├── retrieval.py             # Semantic search over the vector DB
│   ├── student_fetch.py         # HTTP client for mock_student_api
│   ├── pipeline.py               # Orchestrator — retrieval + tool-calling + generation
│   └── main.py                    # Interactive CLI entry point
├── data/
│   └── mock_announcements/  # Fake policy/notice documents (Path A source data)
└── vector_store/            # ChromaDB's persisted files
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```

**Run the mock student data server** (in one terminal):
```bash
uvicorn mock_student_api.main:app --reload
```

**Ingest the mock announcements into the vector DB** (once, or whenever documents change):
```bash
python -m rag_bot.ingest
```

**Start the chatbot** (in another terminal):
```bash
python -m rag_bot.main
```

## Example Queries

- "What's my attendance?"
- "Am I eligible for the exam?"
- "Am I eligible for the Amazon drive?"
- "For which drive am I eligible?"
- "What messages do I have?"
- "When is the holiday?"

## Current Scope & Known Limitations

This is a working prototype built entirely on mock data, pending real UMS/institutional data access from the university:

- **No chunking yet** — mock announcements are short enough that one document = one chunk. Real, longer documents (multi-page policy PDFs) will need chunking before ingestion.
- **Fixed `n_results`** — retrieval currently returns a fixed number of top matches. A distance-based threshold would scale better to a much larger document corpus.
- **No source citation in answers yet** — the model doesn't currently tell the student which specific notice an answer was grounded in.
- **No scheduled re-ingestion** — new announcements must be ingested manually by re-running `ingest.py`. A cron-style scheduler is planned for when live data access is in place.
- **Single-student sessions only** — student ID is entered once per CLI session; there's no real authentication layer (expected, given this stands in for a future login-integrated version).

## Future Work

- Swap `mock_student_api` for real UMS access (only `student_fetch.py`'s base URL should need to change)
- Add chunking for longer real documents
- Add source citations to generated answers
- Add a scheduler for keeping the vector DB current as new announcements are published
