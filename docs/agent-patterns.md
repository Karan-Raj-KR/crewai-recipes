# Agent Design Patterns

Reusable patterns and best practices for designing agents in `crewai-recipes`.

---

## Pattern 1: The Research → Synthesis Pipeline

The most common pattern in this library. A researcher gathers raw information; a synthesiser turns it into something actionable.

```python
researcher = Agent(
    role="Research Specialist",
    goal="Gather accurate, relevant information about X from provided context.",
    backstory="You never fabricate information. If you don't know, you say so.",
    allow_delegation=False,
)

synthesiser = Agent(
    role="Report Writer",
    goal="Transform research into a concise, decision-ready output.",
    backstory="You write for a busy executive who has 60 seconds to read.",
    allow_delegation=False,
)
```

**Used in:** `lead-qualification`, `faq-bot`

---

## Pattern 2: The Classifier → Router Pipeline

Classify an input, then route it to the right handler. Ideal for triage, support, and automation pipelines.

```python
classifier = Agent(
    role="Intent Classifier",
    goal="Classify the input into one of N predefined categories.",
    backstory="You are precise and never guess — LOW confidence is an honest output.",
)

router = Agent(
    role="Action Router",
    goal="Map classified intent to the correct downstream action.",
    backstory="You know every action in the registry and never route to the wrong one.",
)
```

**Used in:** `whatsapp-action-sim`

---

## Pattern 3: Validate → Process → Confirm

For workflows with external state (calendars, CRMs, databases). Validate inputs first to avoid downstream errors.

```python
validator = Agent(role="Input Validator", goal="Ensure all required fields are present and valid.")
processor = Agent(role="Processor", goal="Execute the business logic with validated inputs.")
confirmer = Agent(role="Confirmation Writer", goal="Draft the user-facing confirmation.")
```

**Used in:** `appointment-booking`

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Fix |
|-------------|-------------|-----|
| One agent doing everything | Hard to debug, poor output quality | Split into focused agents |
| Vague `goal` strings | Agent doesn't know what success looks like | Be specific and measurable |
| `allow_delegation=True` on all agents | Creates unpredictable loops | Delegate only when truly needed |
| `temperature=1.0` for factual tasks | High hallucination risk | Use `0.0–0.3` for factual agents |
| Hardcoded API keys in `backstory` | Security risk | Use `os.getenv()` always |

---

## Naming Conventions

- **Agent roles:** `"[Domain] [Function]"` — e.g. `"Lead Research Specialist"`, `"Calendar Availability Manager"`
- **Task descriptions:** Start with an imperative verb — `"Research..."`, `"Score..."`, `"Draft..."`
- **`expected_output`:** Describe the *format and content* precisely — this is what the next agent receives.
