"""
Invoice Extractor Recipe — crew.py

Assembles the 2-agent invoice extraction and audit workflow Crew.
"""

from agents import build_agents
from crewai import Crew, Process
from parser import extract_text_from_pdf_or_image
from tasks import build_tasks


def build_crew(
    invoice_text: str | None = None,
    file_path: str | None = None,
) -> Crew:
    """Build and return the invoice extractor workflow Crew.

    Args:
        invoice_text: Raw text of the invoice document.
        file_path: Optional path to a PDF or image file. If provided and invoice_text is None,
                   extracts text using parser.py.

    Returns:
        A configured Crew instance ready to call .kickoff().

    Raises:
        ValueError: If neither invoice_text nor file_path is provided.
    """
    if not invoice_text and not file_path:
        raise ValueError(
            "Either 'invoice_text' or 'file_path' must be provided to build_crew."
        )

    if not invoice_text and file_path:
        invoice_text, _ = extract_text_from_pdf_or_image(file_path)

    extractor_agent, validator_agent = build_agents()
    tasks = build_tasks(
        extractor_agent=extractor_agent,
        validator_agent=validator_agent,
        invoice_text=invoice_text,
    )

    crew = Crew(
        agents=[extractor_agent, validator_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    return crew
