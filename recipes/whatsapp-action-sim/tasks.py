"""
WhatsApp Action Sim Recipe — tasks.py

Three tasks: intent classification → action routing → response composition.
"""

import json

from crewai import Agent, Task

from action_registry import SUPPORTED_INTENTS, execute_action


def build_tasks(
    intent_agent: Agent,
    router_agent: Agent,
    composer_agent: Agent,
    user_message: str,
    sender_name: str = "User",
) -> list[Task]:
    """Build the WhatsApp message processing task list.

    Args:
        intent_agent: Classifies the intent.
        router_agent: Routes to the correct action.
        composer_agent: Drafts the WhatsApp reply.
        user_message: The incoming WhatsApp message text.
        sender_name: The sender's display name.

    Returns:
        An ordered list of Task objects.
    """
    supported = ", ".join(SUPPORTED_INTENTS)

    intent_task = Task(
        description=(
            f"Incoming WhatsApp message from {sender_name}:\n\n"
            f'  "{user_message}"\n\n'
            f"Classify the primary intent into EXACTLY ONE of: {supported}.\n\n"
            "Rules:\n"
            "1. Output the intent as a single word in ALL CAPS.\n"
            "2. Include a confidence level: HIGH, MEDIUM, or LOW.\n"
            "3. If confidence is LOW or intent is UNKNOWN, note what "
            "   additional info would resolve the ambiguity.\n"
            "4. Extract any key entities (order IDs, dates, product names, etc.)."
        ),
        expected_output=(
            "A structured classification report with:\n"
            "- Intent: <INTENT>\n"
            "- Confidence: HIGH / MEDIUM / LOW\n"
            "- Entities: list of extracted entities\n"
            "- Notes: clarification needed (if any)"
        ),
        agent=intent_agent,
    )

    # Pre-compute a simulated action result so the router has concrete data.
    # In a real pipeline, the router agent would call a tool to do this.
    _simulated_result = execute_action("ORDER_STATUS", user_message)
    simulated_result_json = json.dumps(_simulated_result, indent=2)

    router_task = Task(
        description=(
            "Using the classified intent from the previous task, determine "
            "the correct downstream action and simulate its execution.\n\n"
            "The action registry returned the following simulated payload for "
            "reference (your actual routing should be based on the classified "
            f"intent, not hard-coded to this example):\n\n"
            f"```json\n{simulated_result_json}\n```\n\n"
            "Based on the actual classified intent, describe:\n"
            "1. Which action was triggered.\n"
            "2. What parameters were passed.\n"
            "3. What the simulated response payload contains.\n"
            "4. The recommended next step."
        ),
        expected_output=(
            "A routing report in markdown with sections: "
            "Action Triggered, Parameters, Response Payload (formatted), "
            "and Next Step."
        ),
        agent=router_agent,
        context=[intent_task],
    )

    composer_task = Task(
        description=(
            f"Compose a WhatsApp reply to {sender_name} based on the action "
            "result from the previous task.\n\n"
            "Composition rules:\n"
            "1. Open with the sender's name if known.\n"
            "2. Deliver the core information from the action payload clearly.\n"
            "3. Use 1–2 relevant emojis to add warmth (not excessive).\n"
            "4. Include a clear call-to-action or next step.\n"
            "5. Keep the total message under 200 characters if possible.\n"
            "6. Use line breaks (\\n) to improve readability on mobile.\n\n"
            "Output ONLY the WhatsApp message — no explanations or markdown."
        ),
        expected_output=(
            "A ready-to-send WhatsApp message in plain text with appropriate "
            "line breaks and emoji. No markdown, no quotes around the message."
        ),
        agent=composer_agent,
        context=[intent_task, router_task],
    )

    return [intent_task, router_task, composer_task]
