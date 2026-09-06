"""main.py — Direct entry point for the pr-review-assistant recipe.

Edit repo and pr_number in this file, then run:
    python main.py
"""

from crew import build_crew


def main():
    repo = "Karan-Raj-KR/crewai-recipes"
    pr_number = "187"

    print(f"🔍 Fetching and reviewing PR #{pr_number} in {repo}...\n")

    crew = build_crew(repo=repo, pr_number=pr_number)
    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("GENERATED PR REVIEW COMMENT")
    print("=" * 60)
    print(result.raw)


if __name__ == "__main__":
    main()
