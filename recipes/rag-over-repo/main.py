"""main.py — Direct entry point for the rag-over-repo recipe.

Edit docs_dir and question in this file, then run:
    python main.py
"""

from pathlib import Path

from crew import build_crew
from retriever import DocumentRetriever


def main():
    recipe_dir = Path(__file__).parent.resolve()
    default_docs_dir = recipe_dir / "tests" / "fixtures"

    docs_dir = default_docs_dir
    question = "How do I install the system?"

    print(f"📄 Docs Directory: {docs_dir}")
    print(f"❓ Question: {question}\n")

    # Ingest / retrieve
    retriever = DocumentRetriever(docs_dir)
    retrieval_res = retriever.retrieve(question)

    print(
        f"🔍 Retracted {len(retrieval_res.chunks)} chunks (Cached: {retriever.is_cached})"
    )
    for chunk in retrieval_res.chunks:
        print(f"  • [{chunk.file_path}#{chunk.heading}] (Score: {chunk.score})")

    # Build and run Crew
    crew = build_crew(docs_dir=docs_dir, question=question)
    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(result.raw)


if __name__ == "__main__":
    main()
