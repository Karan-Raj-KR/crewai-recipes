"""ingest.py — Documentation directory parser and chunking utility.

Walks markdown (*.md), text (*.txt), and reStructuredText (*.rst) files in a docs directory,
chunks content by section headings and paragraphs, and extracts metadata.
"""

import hashlib
import json
import os
import re
from pathlib import Path

from models import DocChunk

SUPPORTED_EXTENSIONS = {".md", ".txt", ".rst"}


def find_doc_files(docs_dir: Path) -> list[Path]:
    """Recursively discover supported documentation files."""
    if not docs_dir.exists() or not docs_dir.is_dir():
        raise FileNotFoundError(f"Documentation directory not found: {docs_dir}")

    doc_files = []
    for root, _, files in os.walk(docs_dir):
        # Skip hidden directories like .git or .rag-cache
        if any(part.startswith(".") for part in Path(root).parts):
            continue
        for file_name in files:
            ext = Path(file_name).suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                doc_files.append(Path(root) / file_name)

    return sorted(doc_files)


def extract_chunks_from_markdown(content: str, rel_path: str) -> list[DocChunk]:
    """Parse Markdown content into chunks separated by headings (#, ##, ###)."""
    lines = content.splitlines()
    chunks: list[DocChunk] = []
    current_heading = "General"
    current_lines: list[str] = []

    heading_re = re.compile(r"^(#{1,6})\s+(.+)$")

    for line in lines:
        match = heading_re.match(line)
        if match:
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if chunk_text:
                    chunk_id = hashlib.md5(
                        f"{rel_path}:{current_heading}:{chunk_text[:50]}".encode()
                    ).hexdigest()[:12]
                    chunks.append(
                        DocChunk(
                            chunk_id=chunk_id,
                            file_path=rel_path,
                            heading=current_heading,
                            content=chunk_text,
                        )
                    )
                current_lines = []
            current_heading = match.group(2).strip()
        else:
            current_lines.append(line)

    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunk_id = hashlib.md5(
                f"{rel_path}:{current_heading}:{chunk_text[:50]}".encode()
            ).hexdigest()[:12]
            chunks.append(
                DocChunk(
                    chunk_id=chunk_id,
                    file_path=rel_path,
                    heading=current_heading,
                    content=chunk_text,
                )
            )

    return chunks


def extract_chunks_from_rst(content: str, rel_path: str) -> list[DocChunk]:
    """Parse rST content into chunks by detecting underlined section headers."""
    lines = content.splitlines()
    chunks: list[DocChunk] = []
    current_heading = "General"
    current_lines: list[str] = []

    underline_re = re.compile(r"^([=~\-`:.'\"^_*+#]{3,})$")

    i = 0
    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        if (
            line.strip()
            and underline_re.match(next_line.strip())
            and len(next_line.strip()) >= len(line.strip())
        ):
            # Previous accumulated text forms a chunk
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if chunk_text:
                    chunk_id = hashlib.md5(
                        f"{rel_path}:{current_heading}:{chunk_text[:50]}".encode()
                    ).hexdigest()[:12]
                    chunks.append(
                        DocChunk(
                            chunk_id=chunk_id,
                            file_path=rel_path,
                            heading=current_heading,
                            content=chunk_text,
                        )
                    )
                current_lines = []
            current_heading = line.strip()
            i += 2  # Skip title and underline
            continue
        else:
            current_lines.append(line)
            i += 1

    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunk_id = hashlib.md5(
                f"{rel_path}:{current_heading}:{chunk_text[:50]}".encode()
            ).hexdigest()[:12]
            chunks.append(
                DocChunk(
                    chunk_id=chunk_id,
                    file_path=rel_path,
                    heading=current_heading,
                    content=chunk_text,
                )
            )

    return chunks


def extract_chunks_from_txt(content: str, rel_path: str) -> list[DocChunk]:
    """Parse plain text files into paragraph-based chunks."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    chunks: list[DocChunk] = []

    for idx, para in enumerate(paragraphs, 1):
        heading = f"Paragraph {idx}"
        chunk_id = hashlib.md5(
            f"{rel_path}:{heading}:{para[:50]}".encode()
        ).hexdigest()[:12]
        chunks.append(
            DocChunk(
                chunk_id=chunk_id, file_path=rel_path, heading=heading, content=para
            )
        )

    return chunks


def parse_doc_file(file_path: Path, docs_dir: Path) -> list[DocChunk]:
    """Parse a single documentation file into chunks based on its extension."""
    rel_path = str(file_path.relative_to(docs_dir))
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        print(f"Warning: Could not read file {file_path}: {e}")
        return []

    ext = file_path.suffix.lower()
    if ext == ".md":
        return extract_chunks_from_markdown(content, rel_path)
    elif ext == ".rst":
        return extract_chunks_from_rst(content, rel_path)
    else:
        return extract_chunks_from_txt(content, rel_path)


def compute_docs_hash(doc_files: list[Path]) -> str:
    """Compute a composite hash of all doc files to detect content updates."""
    hasher = hashlib.sha256()
    for f in doc_files:
        hasher.update(str(f).encode())
        hasher.update(str(f.stat().st_mtime).encode())
        hasher.update(str(f.stat().st_size).encode())
    return hasher.hexdigest()[:16]


def ingest_docs_directory(
    docs_dir: Path, cache_dir: Path | None = None
) -> tuple[list[DocChunk], bool]:
    """Parse all documentation files in docs_dir with local caching in .rag-cache/.

    Returns:
        Tuple of (list of DocChunks, is_from_cache boolean).
    """
    docs_path = Path(docs_dir).resolve()
    doc_files = find_doc_files(docs_path)

    if not doc_files:
        return [], False

    if cache_dir is None:
        cache_dir = docs_path / ".rag-cache"

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "doc_chunks_cache.json"

    current_hash = compute_docs_hash(doc_files)

    if cache_file.exists():
        try:
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            if cache_data.get("docs_hash") == current_hash and "chunks" in cache_data:
                chunks = [DocChunk(**item) for item in cache_data["chunks"]]
                return chunks, True
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            pass  # Fall back to re-ingesting on corrupt cache

    all_chunks: list[DocChunk] = []
    for file_path in doc_files:
        file_chunks = parse_doc_file(file_path, docs_path)
        all_chunks.extend(file_chunks)

    # Save to cache
    try:
        cache_payload = {
            "docs_hash": current_hash,
            "chunks": [chunk.model_dump() for chunk in all_chunks],
        }
        cache_file.write_text(json.dumps(cache_payload, indent=2), encoding="utf-8")
    except OSError as e:
        print(f"Warning: Could not write cache file: {e}")

    return all_chunks, False
