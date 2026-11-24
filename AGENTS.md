# Agent Instructions — {{PROJECT_NAME}}

> **This is the master file.** `CLAUDE.md` and `GEMINI.md` are symlinks to this file.
> Edit ONLY `AGENTS.md` — changes propagate automatically.
> NEVER break the symlink structure.

---

## Critical Production Rules

### 1. Read-Only Mode (ABSOLUTE)

**Default access to production resources is read-only.** On a shared host, an agent may
edit and test in its own development clone within the requested task. The rules below
cover the live deployment, production data and host administration.

The agent MUST NOT perform any of these actions without explicit user permission:
- Install or remove software
- Modify configuration files (`.env`, service units, reverse proxy configs)
- Create, modify, or delete files in the live deployment
- Start, stop, or restart any service
- Run database migrations or write to databases
- Create, modify, or remove system users
- Modify firewall rules or network configuration

If a production change falls outside the user's explicit authorization, describe its
scope and impact and wait for approval. An approval covers the steps you named, nothing
more: an extra check or fix on the host goes back to the user first.

### 2. SSH Connection Failures

On an authentication failure, stop and check the intended host, user and key before
trying again. Repeated failed logins can trigger a ban. If the host key changes, verify
its fingerprint through a trusted channel before reconnecting.

During an approved reboot, a refused connection or timeout is expected. Retry the
same SSH configuration at a bounded interval (for example, every 10 seconds for up
to two minutes). Report the last error if the host does not return.

### 3. Database Migrations / Schema Changes

Use the project's schema ownership and migration configuration to identify the target
database(s). Confirm the environment and aliases before applying the migration.
Verify the migration state on each intended target.

### 4. Configuration Comments

**ENGLISH ONLY (ASCII)** in all configuration files:
- `.env` files
- Service unit files (systemd, supervisor, etc.)
- Shell scripts (`.sh`)
- Reverse proxy configs (nginx, caddy, traefik, etc.)
- Docker/Compose files
- CI/CD pipeline configs

Non-ASCII characters (Russian, Chinese, etc.) cause encoding issues in system services.

### 5. Timezone Awareness

**ALWAYS use the project-configured timezone** for:
- Scheduled tasks (cron, task queues, schedulers)
- Log analysis and timestamp comparisons
- Database queries with time filters

Never assume UTC unless the project explicitly uses it.

### 6. Application Startup

Verify the app still starts after every change. A feature that works in isolation and breaks
boot is worse than one that was never added.

### 7. Production Database Reads

Only via `diag-sql` and its query rules (`docs/AGENT_SERVER_ACCESS.md`), never a client over SSH
or against a remote host: a read-only query can still take a database down.

### 8. Credentials

Use only the access set up for the task; ask the user for anything else. Never search for
credentials (password managers, SSH agent, keychain). Guard: `.claude/hooks/`.

---

## Project requirements

Clarify an ambiguous requirement, name or external contract before implementing a
change that depends on it. Cross-project working agreements are available in the
optional [user defaults](agent-defaults/AGENTS.md).

---

## Documentation Maintenance (MANDATORY)

After ANY code change, update the relevant documentation:

| Change Type | Update These Files |
|-------------|-------------------|
| Schema / data model changes | Relevant data model docs |
| Architecture / module-boundary changes | `docs/ARCHITECTURE.md` + add an ADR in `docs/decisions/` |
| API endpoint changes | `docs/API_REFERENCE.md` |
| New environment variables | App config + `.env.example` + `docs/ENV_VARIABLES.md` |
| Background task changes | `docs/BACKGROUND_TASKS.md` |
| Deployment changes | `docs/DEPLOYMENT_GUIDE.md` |
| Any change | `CHANGELOG.md` |

> **Per-iteration specs, plans, and checkpoints live in the gitignored `.context/`, not in the
> repo.** The committed docs describe what the system *is*; `.context/` holds the working notes for
> how it's being changed right now.

---

## Documentation Map

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Master agent instructions, always-on (this file) |
| `.claude/skills/` | On-demand agent knowledge — catalogues, runbooks, subsystem mechanics |
| `.claude/hooks/` | Optional guards for the production and credential rules |
| `README.md` | Project overview, setup, architecture |
| `docs/ARCHITECTURE.md` | Living system specification (what it does and is made of) |
| `docs/decisions/` | Architecture Decision Records — the "why" behind decisions |
| `CHANGELOG.md` | Complete change history |
| `.env.example` | Environment variables template |
| `docs/ENV_VARIABLES.md` | Authoritative env vars reference |
| `docs/API_REFERENCE.md` | API endpoints documentation |
| `docs/DEPLOYMENT_GUIDE.md` | CI/CD and deployment procedures |
| `docs/TESTING.md` | Test structure, running tests, coverage |
| `docs/COMMON_PITFALLS.md` | Known issues and solutions |
| `docs/AGENT_SERVER_ACCESS.md` | Diagnostic vs. Investigation mode |
| `docs/DIAG_USER_SETUP.md` | Read-only diagnostic user runbook |
| `docs/PRODUCTION_OPERATIONS.md` | Server operations reference |
| `docs/BACKGROUND_TASKS.md` | Background/scheduled tasks configuration |

---

## Architecture Overview

### Configuration Hierarchy (3 layers)

| Layer | Source | Purpose | Editable By |
|-------|--------|---------|-------------|
| 1 | `.env` / secrets manager | Secrets, credentials, connection strings | DevOps / manual |
| 2 | Database / config store | Business logic, feature flags, thresholds | Admin UI / API |
| 3 | Runtime | One-time overrides, CLI flags | Developer |

### Environment Configuration

- Read env vars via your framework's recommended method
- All secrets go in `.env` (listed in `.gitignore`) or a secrets manager
- Never hardcode secrets in code or documentation

### Database Setup

<!-- Customize for your project -->
| Alias | Database Name | Purpose |
|-------|--------------|---------|
| `primary` | `{{DB_NAME}}` | Main application database |
<!-- Add more databases as needed -->

### Key Integrations

<!-- One line per external service: data store, cache/broker, payments, alerts, storage, analytics -->
| Name | Role | Docs |
|------|------|------|

---

## Development Workflow

### Branch Naming

```
feature/issue-X-description
fix/issue-X-description
hotfix/description
```

### Commit Messages

Link GitHub/Linear issues:
```
fix: resolve webhook timeout (#42)
feat: add user search endpoint (#55)
```

### Testing

```bash
# Run all tests
{{TEST_COMMAND}}

# Run specific test file
{{TEST_COMMAND_SPECIFIC}}

# Run with coverage
{{TEST_COMMAND_COVERAGE}}
```

**Coverage target**: {{COVERAGE_TARGET}}% minimum

### Pre-merge Checklist

- [ ] All tests pass
- [ ] Coverage meets minimum threshold
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated
- [ ] No hardcoded secrets
- [ ] No debug prints or TODO comments
- [ ] Type checking passes (if applicable)

---

## Server Access

Two modes, details in `docs/AGENT_SERVER_ACCESS.md`: Diagnostic (`diag`, read-only: logs, status,
`diag-sql`) and Investigation (`{{DEPLOY_USER}}`, every change with permission). **Default**: start in
Diagnostic Mode; escalate only when read-only is insufficient.

---

## Operations

Health checks, service status, log locations and disk checks — `docs/PRODUCTION_OPERATIONS.md`.
Known issues and their fixes — `docs/COMMON_PITFALLS.md`.

Deliberately not duplicated here: these are commands you reach for during an incident, not
facts you need on every turn. Once the project has real runbooks, they belong in
`.claude/skills/` so they load with the task that needs them.

---

## What belongs in this file

Everything here is loaded into **every turn of every session**, forever. That budget is the
scarce resource, so this file earns its size by holding only what is true regardless of the
task: what the project is, the always-on rules, the non-obvious gotchas with their reasons,
and pointers to where the rest lives.

Everything else goes in `.claude/skills/`, which the agent loads **on demand**. Only a skill's
one-line `description` costs context until something matches it. See
[`.claude/skills/README.md`](.claude/skills/README.md).

**Tripwire: if this file passes ~10 KB, something in it is a skill.** Left alone, an agent file
only grows — every incident and integration gets appended, nothing is ever removed, and the
result is a 40–80 KB file where the useful 5 KB is buried. Measure by section; the offender is
usually one heading at a third of the total.

When starting a project, remove the stacks, access modes and tables it does not use.

Move out: anything shaped "here are N similar subsystems" (integrations, providers, accounts,
environments) — only one is ever relevant at a time. And any procedure that fires on a task
rather than on every turn: diagnostic protocols, release checklists, review checklists.

Three things that must never go in this file or any skill, because each one goes wrong
silently and confidently:

- **Line numbers.** `handlers.py:88` is wrong by the next refactor and there is no signal when
  it breaks. Name the function or the file; let the agent grep.
- **Business data copied from code.** Prices, plans, discount codes, feature flags, endpoint
  inventories. The code is the source of truth; a copy diverges within weeks and then answers
  confidently with last quarter's numbers.
- **Status markers and plans.** "Phase 2 in progress", unticked checklists, "current
  status". They are true for a week and misleading for years. Per-iteration notes belong in the
  gitignored `.context/`; finished history belongs in `CHANGELOG.md`.

If a rule here contradicts the code, the code wins — say so and fix this file rather than
working around it.
