# 📝 Meeting Notes Summariser

Turn a meeting transcript into structured decisions, action items, risks, open questions, and a ready-to-send follow-up email, using two agents in a sequential CrewAI crew.

---

## What It Does

```
Meeting transcript (.md / .txt)
  │
  ▼
┌──────────────────────────────┐
│  Meeting Notes Extractor     │  → decisions, action items (owner + due date),
│                              │    risks & blockers, open questions
└──────┬───────────────────────┘
       │  context=[extract_task]
       ▼
┌──────────────────────────────┐
│  Email Drafter               │  → short follow-up email: recap, action items
│                              │    with owners, open questions
└──────┬───────────────────────┘
       │
       ▼
  Markdown (default) or validated JSON (--json)
```

The extractor never invents owners or due dates. Anything the notes don't state is returned as `null` and rendered as `TBD`.

---

## Quick Start

```bash
cd recipes/meeting-notes-summariser
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

Get a free key at [build.nvidia.com](https://build.nvidia.com).

---

## Run

### CLI mode

```bash
# Markdown summary + email draft
python run.py --transcript path/to/notes.md

# Validated JSON (stdout contains only the JSON; logs go to stderr)
python run.py --transcript path/to/notes.md --json > summary.json
```

`--transcript` accepts any UTF-8 plain-text file (`.md`, `.txt`, ...). Binary formats such as `.docx` or `.pdf` are not supported.

### Built-in samples

```bash
python main.py
```

Runs a detailed sample meeting through the crew. Edit the toggle in `main.py` to try the vague sample (no owners, no dates) and confirm nothing gets invented.

### In the Playground

The playground picks this recipe up automatically and shows one input, **Meeting Transcript or Notes**. Paste the transcript text and run.

### Tests (offline, no API key needed)

```bash
pytest test_main.py -v
```

---

## Output Schema

`--json` prints a `MeetingNotesResult` (see `models.py`):

| Field | Type | Notes |
|-------|------|-------|
| `summary.decisions` | `list[str]` | Decisions taken |
| `summary.action_items` | `list[ActionItem]` | `task`, optional `owner`, optional `due_date` (kept as stated, e.g. `"next Friday"`) |
| `summary.risks_blockers` | `list[str]` | Risks and blockers raised |
| `summary.open_questions` | `list[str]` | Questions left unresolved |
| `email.subject` | `str` | Follow-up email subject |
| `email.body` | `str` | Plain-text follow-up email body |

Placeholder values the model might emit (`"N/A"`, `"TBD"`, `"Not specified"`) are normalised to `null`, and list entries are trimmed and de-duplicated.

---

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Extractor and Drafter agents (also raises `max_tokens`, see Troubleshooting) |
| `tasks.py` | `extract_task` (→ `MeetingSummary`) and `draft_task` (→ `FollowUpEmail`, chained with `context=[extract_task]`) |
| `crew.py` | `build_crew(transcript)`, a sequential crew; the parameter matches the `transcript` key in `inputs.json` |
| `models.py` | Pydantic models for structured output |
| `run.py` | CLI: `--transcript`, `--json`, markdown rendering |
| `main.py` | Runs built-in sample transcripts |
| `inputs.json` | Playground input definition |
| `llm.py` | Shared LLM config, copied verbatim, do not edit |
| `test_main.py` | Offline structural tests (crew shape, context chaining, models) |

---

## Expected Output

Running `python main.py` on the built-in sample meeting (about 240 words) produces:

```
# Meeting Summary

## Decisions
- Beta launch is still targeted for 16 November.
- Drop the optional "invite teammates" step from the first release and ship it in v1.1 instead.
- Freeze new feature requests until after the beta launch.

## Action Items
- Finish the new billing integration — **Owner:** Marcus | **Due:** Wednesday 4 November
- Update the Figma files and hand them to Marcus — **Owner:** Elena | **Due:** Friday 30 October
- Investigate the flaky test environment and report back — **Owner:** Tom | **Due:** Tuesday 3 November
- Communicate the freeze to stakeholders — **Owner:** Priya | **Due:** end of day today

## Risks & Blockers
- Payment provider has not delivered sandbox credentials after waiting a week, which is the biggest risk to the beta launch date.
- Test environment is flaky and has failed nightly runs three times this week.
- If the test environment is not stable by 9 November, QA sign-off will be at risk.

## Open Questions
- Who is responsible for the beta announcement blog post?
- Does legal need to review the updated terms of service before launch?
- Has the support team been trained on the new billing screens?

---

# Follow-up Email Draft

**Subject:** Follow-up: Beta Launch Meeting - Decisions and Next Steps

Hi team,

Here is a summary of today's meeting:

Decisions:
- Beta launch is still targeted for 16 November.
- Drop the optional "invite teammates" step from the first release and ship it in v1.1 instead.
- Freeze new feature requests until after the beta launch.

Action items:
- Finish the new billing integration - Marcus - due Wednesday 4 November
- Update the Figma files and hand them to Marcus - Elena - due Friday 30 October
- Investigate the flaky test environment and report back - Tom - due Tuesday 3 November
- Communicate the freeze to stakeholders - Priya - due end of day today

Open questions:
- Who is responsible for the beta announcement blog post?
- Does legal need to review the updated terms of service before launch?
- Has the support team been trained on the new billing screens?

Please let me know if anything is missing.

Best regards
```

---

## Troubleshooting

- **`Could not parse response content as the length limit was reached`:** the model spent its whole token budget on reasoning before writing the structured answer. The shared `llm.py` caps output at 2048 tokens, so `agents.py` raises `max_tokens` to 8192 on the LLM instance. If you still hit it, raise that value (for example 16384) or switch `LLM_MODEL` in `.env`.
- **`❌ Error: the model's output could not be parsed into the expected structure`:** the model returned text that doesn't match the schema. `run.py` prints the raw outputs of both agents to stderr so you can see what came back. Retrying often helps; a more capable model helps more.
- **`ValueError: transcript must not be empty`:** the transcript file or playground input was blank.
- **`❌ Error: could not read ...`:** the file isn't UTF-8 text. Convert it to `.txt` or `.md` first.
- **`EnvironmentError: LLM_API_KEY is not set`:** add your key to `.env` (copy from `.env.example`).
- **`ModuleNotFoundError: llm`:** `llm.py` is missing. Copy it verbatim from another recipe (for example `lead-qualification`).

---

## Contributing

Please read [CONTRIBUTING.md](../../CONTRIBUTING.md) before opening a PR. This recipe:

- ✅ Runs end-to-end from a fresh venv
- ✅ Passes `ruff check` and `ruff format`
- ✅ Has a complete `README.md` with expected output
- ✅ Keeps `llm.py` unchanged (copied verbatim)
- ✅ Aligns the `build_crew()` signature with the `inputs.json` keys