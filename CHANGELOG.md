# Changelog — {{PROJECT_NAME}}

All notable changes to this project are documented in this file.

Format: `## [YYYY-MM-DD] Summary` with bullet points for details.

---

## [2026-11-24] Agent user defaults and VPS example

- Split cross-project working agreements into an optional user instructions file and documented two independent agent accounts on an always-on VPS.
- Clarified SSH recovery during a planned reboot and how to select and verify database migration targets.

---

## [2026-05-31] Backported Stack-Agnostic Runbook Conventions

- Added ADR journal at `docs/decisions/` with `README.md`, `0000-adr-template.md`, and `0001-two-user-access-model.md`
- Added living architecture specification at `docs/ARCHITECTURE.md`
- Added Working Principles section to `AGENTS.md`
- Added `.context/` convention (gitignored local context directory)

---

## [{{DATE}}] Initial Setup

- Project structure created
- Agent instructions configured (AGENTS.md)
- Documentation templates added
- CI/CD workflows configured

## [2026-08-07] Progressive Disclosure for Agent Knowledge

- Added `.claude/skills/` with a `README.md` (when a skill is warranted, where it belongs, how to size it) and a copy-me `_template/SKILL.md`. The template previously had only an always-on layer, so every project seeded from it grew its `AGENTS.md` monotonically.
- `AGENTS.md`: new "What belongs in this file" section with a ~10 KB tripwire, and the three things that must never be written into an agent file — line numbers, business data copied from code, and status markers.
- Removed the "Latest Updates" section and the documentation-maintenance row that regrew it. It duplicated `CHANGELOG.md`.
- Replaced the "Operations Quick Reference" command dump with pointers to `docs/PRODUCTION_OPERATIONS.md` and `docs/COMMON_PITFALLS.md`. It also used a `{{LOG_PATH}}` placeholder that `README.md` never defined — the real one is `{{APP_LOG_PATH}}`.
- Dropped production rule 7 ("External Service Dependencies"), which restated general engineering practice.
