"""
WhatsApp Action Sim Recipe — action_registry.py

Simulated action registry — maps intents to mock API responses.
In a real system, each action would call an actual API endpoint.
"""

from typing import Any


# Supported intents
SUPPORTED_INTENTS: list[str] = [
    "ORDER_STATUS",
    "BOOK_APPOINTMENT",
    "FAQ",
    "COMPLAINT",
    "FEEDBACK",
    "HUMAN_ESCALATION",
    "UNKNOWN",
]


def execute_action(intent: str, message: str) -> dict[str, Any]:
    """Execute the simulated action for a given intent.

    Args:
        intent: The classified intent string.
        message: The original user message (for context).

    Returns:
        A dict with keys: action, status, payload, and next_step.
    """
    intent_upper = intent.strip().upper()

    if intent_upper == "ORDER_STATUS":
        return {
            "action": "GET_ORDER_STATUS",
            "status": "success",
            "payload": {
                "order_id": "ORD-78421",
                "status": "Out for Delivery",
                "estimated_arrival": "Today by 6:00 PM",
                "carrier": "BlueDart",
                "tracking_url": "https://track.example.com/ORD-78421",
            },
            "next_step": "Send order status to user",
        }

    if intent_upper == "BOOK_APPOINTMENT":
        return {
            "action": "INITIATE_BOOKING_FLOW",
            "status": "success",
            "payload": {
                "flow": "appointment_booking",
                "available_slots": [
                    "Tomorrow 10:00 AM",
                    "Tomorrow 3:00 PM",
                    "Day after 11:00 AM",
                ],
            },
            "next_step": "Present slot options to user",
        }

    if intent_upper == "FAQ":
        return {
            "action": "SEARCH_FAQ",
            "status": "success",
            "payload": {
                "matched": True,
                "answer": (
                    "Our return window is 30 days from delivery. "
                    "Items must be unused and in original packaging."
                ),
            },
            "next_step": "Return FAQ answer to user",
        }

    if intent_upper == "COMPLAINT":
        return {
            "action": "CREATE_COMPLAINT_TICKET",
            "status": "success",
            "payload": {
                "ticket_id": "TKT-20394",
                "priority": "High",
                "assigned_to": "Customer Success Team",
                "expected_response": "Within 4 hours",
            },
            "next_step": "Confirm ticket creation to user",
        }

    if intent_upper == "FEEDBACK":
        return {
            "action": "LOG_FEEDBACK",
            "status": "success",
            "payload": {
                "feedback_id": "FB-5521",
                "logged": True,
                "thank_you_reward": "5% off your next order",
            },
            "next_step": "Thank user and share reward",
        }

    if intent_upper == "HUMAN_ESCALATION":
        return {
            "action": "ESCALATE_TO_HUMAN",
            "status": "success",
            "payload": {
                "queue": "live_support",
                "estimated_wait": "3 minutes",
                "agent_name": "Support Team",
            },
            "next_step": "Connect user to live agent",
        }

    # UNKNOWN or unrecognised intent
    return {
        "action": "LOG_UNKNOWN",
        "status": "fallback",
        "payload": {
            "message": message,
            "suggestion": "Route to human agent",
        },
        "next_step": "Ask user to clarify or escalate",
    }
