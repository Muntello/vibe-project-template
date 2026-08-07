# Project skills

On-demand knowledge for AI agents working in this repository. `AGENTS.md` is loaded on every
turn; a skill here is loaded only when the task matches its `description`.

That difference is the whole point. Ten skills of 6 KB each cost the same as one line of
`AGENTS.md` until one of them is actually needed.

Both Claude Code and Codex read the same format, from `.claude/skills/` and `.codex/skills/`
respectively. Symlink one to the other if the project uses both.

## When to create one

When something in `AGENTS.md` is only true for a particular task. The usual candidates:

- **Catalogues** — "here are the six payment providers", "here are the four ad accounts". Only
  one matters at a time, so loading all six on every turn is waste.
- **Procedures** — production diagnostics, a release checklist, a pre-deploy review, an
  incident runbook. They fire on a task, not on every turn.
- **Hard-won mechanics** — the traps in one subsystem, with the incident that revealed each.

Not a candidate: general engineering advice the model already has, or a constraint that must
hold in every session — that is an always-on rule and belongs in `AGENTS.md`.

## Where a skill lives

**A skill lives where it can go stale.** Anything that goes stale against this repository's
schema, commands or incidents belongs here, in this directory, so it travels in the same
commit as the migration that renames the column. Knowledge that goes stale against nothing in
particular belongs in a shared library instead.

## Writing one

Copy `_template/SKILL.md` into a new directory named after the skill.

The `description` is the entire interface: it is the only text the agent reads before deciding
whether to load the body. Write the phrasings people actually type, in every language they type
them in — not marketing copy.

Two habits that make the difference between a skill that helps and one that misleads:

- **State the fact, then the failure it causes.** "Dedup is on `SHA256(raw body)`" is trivia.
  "…not an event id, because the provider sends none — so two distinct events with identical
  bodies collapse into one" is usable.
- **Keep the reason, drop the shouting.** "One failed attempt is safe; the second one is not"
  generalizes to cases you did not enumerate. "🚨 CRITICAL: DO NOT retry" does not.

Record what is a deliberate absence, too. Anything that looks like a missing feature will
eventually be "fixed" by someone — including an agent — unless the omission is written down as
a decision.

## Sizing

A task should pull one skill, not three. If a skill routinely needs two others, the split
follows the wrong seam — split by what gets loaded together, not by topic name.

Past ~10 KB, break the body into a thin index plus `references/` files, one per group of things
touched by the same task.
