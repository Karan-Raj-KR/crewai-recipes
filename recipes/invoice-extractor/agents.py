"""
Invoice Extractor Recipe — agents.py

Defines the Extractor Agent and Validator Agent for structured document parsing and financial auditing.
"""

from crewai import Agent
from llm import get_llm


def build_agents() -> tuple[Agent, Agent]:
    """Build and return the Extractor and Validator agents.

    Returns:
        A tuple of (extractor_agent, validator_agent).
    """
    llm = get_llm()

    extractor_agent = Agent(
        role="Senior Invoice Parsing Specialist",
        goal=(
            "Extract structured data from raw invoice text, including vendor details, "
            "invoice number, dates, individual line items (description, quantity, unit price, line total), "
            "subtotal, tax, and grand total."
        ),
        backstory=(
            "You are an expert accounts payable automation agent with years of experience "
            "parsing complex, noisy invoice documents and receipts. You accurately extract "
            "every line item and numeric value without missing details."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    validator_agent = Agent(
        role="Lead Financial Auditor & Validation Specialist",
        goal=(
            "Audit the extracted invoice data to verify that line item totals match quantity * unit price, "
            "and that subtotal + tax equals the grand total. Flag any arithmetic discrepancies or missing "
            "fields as informative audit warnings without breaking execution."
        ),
        backstory=(
            "You are a meticulous CPA and financial auditor. You cross-check invoice math, "
            "detecting discrepancy errors between item sums and totals while compiling clear, "
            "actionable warning reports for finance teams."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    return extractor_agent, validator_agent
