# AGENTS.md — Facturación MTM

Instructions for AI agents working in this repository. They apply to planning, implementation,
debugging, reviews, progress updates and handovers. Read this before starting work.

## Communication

- Be concise, direct and informative. No walls of text, filler, generic acknowledgements or repeated
  summaries.
- Lead with the answer or conclusion. Prefer short paragraphs and a few focused bullets.
- Do not over-explain routine details or familiar concepts. Explain jargon and metrics in plain
  language when they matter to the decision.
- Never sacrifice accuracy, context or technical detail for brevity. Conciseness applies to the
  message, not to the work: still investigate, implement and verify fully.

### Reporting to the owner

- Write every report, summary and update for the project owner.
- Answer the actual question in the first one or two sentences.
- Separate what changed, what stayed the same, and what was intentionally preserved.
- Translate findings into practical implications; say what numbers mean when it matters.
- Distinguish verified facts from assumptions and estimates.
- Do not present activity as progress unless it produced a relevant result.
- Include paths or evidence only when they help the owner understand or verify the result.

### Questions and decisions

- Inspect the project and docs first; only ask when the answer is genuinely needed or belongs to the
  owner.
- When offering alternatives, explain the practical difference and recommend one when there is a
  clear best choice.
- Make low-risk implementation decisions independently, consistent with existing conventions.
- Do not silently make significant design, scope or content decisions that need owner approval.
- State required decisions plainly; numbered options help when they genuinely clarify.

### Progress and handovers

- Keep updates short: meaningful changes, blockers, findings, next step.
- For finished work, summarise the outcome; for unfinished work, say what remains and whether it
  needs owner input.
- Do not duplicate large doc sections; reference the file or section instead.
- End with a clear next step, or say no further action is needed.

## Project rules

- **64-bit Windows only.** Windows 10 64-bit 1809+ / Windows 11. Never imply 32-bit support.
- **Do not change output formats or business rules**: claim Excel (10 columns, one sheet per day),
  BULK UPLOAD, driverlog DOCX/PDF. Engine changes need explicit owner approval.
- **Never modify originals**: the claim, the BULK template, the driverlog templates.
- **Do not experiment with production data.** Use `tests/fixtures.py` or `data/test/`; never read,
  copy or modify `data/base/` for testing.
- **No claims without evidence.** Run the tests/build and report real results.
- **Commit and push are authorized** by the owner (granted 2026-11-14).
- Driverlog PDFs need Microsoft Word installed (COM export); merging existing PDFs does not.

## Where things live

- `docs/NOTES.md` — current source of truth: business rules, outputs, commands.
- `docs/PU_TIME_FINDINGS.md` — PU/DropOff calibration.
- `docs/PORTABILITY.md`, `docs/PYSIDE6_UI_MIGRATION_ANALYSIS.md` — build and UI history (32-bit
  sections are historical).
- `README.md` — setup, usage, structure.
