# RAG Over Repo (Document Q&A with Citations)

Ingest documentation files (`*.md`, `*.txt`, `*.rst`) from any local directory or repository, index section headings and content chunks, retrieve top-k relevant context, and generate precise technical answers complete with inline citations (`[file_path#heading]`).

If the retrieved documentation chunks do not contain the answer, the model explicitly refuses to answer (`"I don't know based on the provided docs"`) to eliminate hallucinations.

---

## Features

- **Multi-Format Ingestion**: Parses `.md` headers (`#`, `##`), `.rst` section underlines, and `.txt` paragraphs.
- **Local Embedding & Caching**: Caches document chunks and pre-calculated index in `.rag-cache/` inside the target docs directory for instant re-runs.
- **Inline Citations**: Every answer incorporates precise citations in `[filename.ext#Header]` format.
- **Strict Anti-Hallucination**: Returns explicit refusal if requested info is outside the provided documentation.
- **Zero Heavy Servers**: Pure local TF-IDF & Cosine Similarity vector engine — no Docker or external vector DB server required.

---

## Input / Output Schema

### Input Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `--docs-dir` | String | Yes | Path to directory containing documentation files (`*.md`, `*.txt`, `*.rst`). |
| `--question` | String | Yes | User question or query. |
| `--top-k` | Integer | No | Number of document chunks to retrieve (Default: `4`). |
| `--pretty` | Flag | No | Output pretty-printed human-readable text instead of JSON. |

### Output JSON Schema (`RAGAnswer`)

```json
{
  "question": "How do I install the system?",
  "answer": "To install the system, clone the repository using `git clone` and install dependencies with `pip install -r requirements.txt` [installation.txt#System Installation Guide]. Then run database migrations [installation.txt#System Installation Guide].",
  "citations": [
    {
      "file_path": "installation.txt",
      "heading": "System Installation Guide"
    }
  ],
  "refused": false
}
```

---

## Setup & Running

### 1. Configure Environment

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
LLM_API_KEY=your-api-key-here
```

### 2. Run with Sample Fixtures

```bash
python run.py --docs-dir tests/fixtures --question "How do I install the system?" --pretty
```

### 3. Run with Custom Repository Docs

```bash
python run.py --docs-dir ../../docs --question "How do I write a new recipe?" --pretty
```

---

## Local Caching & Disk Space Management

- **Cache Location**: On first run, parsed document chunks and TF-IDF index are stored in `.rag-cache/doc_chunks_cache.json` within the specified `--docs-dir`.
- **Cache Invalidation**: Automatically re-ingests documentation if any file's modification timestamp or content size changes.
- **Disk Space Cost**: Very minimal (typically <50 KB for medium doc sets).
- **Clearing Cache**: To force a complete re-index, delete the `.rag-cache/` directory:

```bash
rm -rf path/to/docs/.rag-cache
```

---

## Testing

Run unit tests against sample fixtures:

```bash
pytest test_rag_over_repo.py -v
```
