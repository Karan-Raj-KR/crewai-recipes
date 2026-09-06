"""run.py — CLI entry point for the rag-over-repo recipe.

Usage:
    python run.py --docs-dir path/to/docs --question "How do I install the system?"
    python run.py --docs-dir path/to/docs --question "What is the capital of France?" --pretty
"""

import argparse
import json
import sys
from pathlib import Path

from crew import build_crew
from llm import get_llm
from models import RAGAnswer
from retriever import DocumentRetriever


def parse_args():
    parser = argparse.ArgumentParser(
        description="RAG Over Repo — Ingest repository docs and answer questions with citations."
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default=str(Path(__file__).parent / "tests" / "fixtures"),
        help="Path to directory containing documentation files (*.md, *.txt, *.rst).",
    )
    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help="User question to answer based on documentation.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of document chunks to retrieve (default: 4).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Format output nicely for human reading.",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        help="Optional path to write output JSON.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    docs_path = Path(
        args.docs - dir if hasattr(args, "docs-dir") else args.docs_dir
    ).resolve()
    if not docs_path.exists():
        print(f"Error: Documentation directory not found: {docs_path}", file=sys.stderr)
        sys.exit(1)

    try:
        llm = get_llm()
    except OSError as e:
        print(f"Environment Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"⚡ Ingesting/Retrieving docs from: {docs_path}")
    retriever = DocumentRetriever(docs_path)
    retrieval_res = retriever.retrieve(args.question, top_k=args.top_k)

    if not retrieval_res.chunks:
        refusal_answer = RAGAnswer(
            question=args.question,
            answer="I don't know based on the provided docs.",
            citations=[],
            refused=True,
        )
        if args.pretty:
            print("\n" + "=" * 60)
            print("RAG OVER REPO ANSWER")
            print("=" * 60)
            print("Answer: I don't know based on the provided docs.")
            print("Status: Refused (No documentation chunks found)")
        else:
            print(json.dumps(refusal_answer.model_dump(), indent=2))
        return

    print(
        f"🔍 Found {len(retrieval_res.chunks)} relevant chunks (Cached: {retriever.is_cached})"
    )
    for c in retrieval_res.chunks:
        print(f"  • [{c.file_path}#{c.heading}] (Score: {c.score})")

    crew = build_crew(
        docs_dir=docs_path,
        question=args.question,
        top_k=args.top_k,
        llm=llm,
    )
    result = crew.kickoff()
    raw_answer = str(result.raw).strip()

    is_refusal = "don't know based on the provided docs" in raw_answer.lower()
    citations = retriever.extract_citations(
        retrieval_res.chunks if not is_refusal else []
    )

    answer_obj = RAGAnswer(
        question=args.question,
        answer=raw_answer,
        citations=citations,
        refused=is_refusal,
    )

    if args.pretty:
        print("\n" + "=" * 60)
        print("RAG OVER REPO ANSWER")
        print("=" * 60)
        print(raw_answer)
        print("\nSources Cited:")
        if citations:
            for cit in citations:
                print(f"  - {cit.file_path}#{cit.heading}")
        else:
            print("  (None)")
    else:
        print(json.dumps(answer_obj.model_dump(), indent=2))

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(answer_obj.model_dump(), indent=2), encoding="utf-8"
        )
        print(f"\nSaved output JSON to: {out_path}")


if __name__ == "__main__":
    main()
