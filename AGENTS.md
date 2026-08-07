# Agent Instructions — {{PROJECT_NAME}}

> **This is the master file.** `CLAUDE.md` and `GEMINI.md` are symlinks to this file.
> Edit ONLY `AGENTS.md` — changes propagate automatically.
> NEVER break the symlink structure.

---

## Critical Production Rules

### 1. Read-Only Mode (ABSOLUTE)

**Default behavior on production servers: READ ONLY.**

The agent MUST NOT perform any of these actions without explicit user permission:
- Install or remove software
- Modify configuration files (`.env`, service units, reverse proxy configs)
- Create, modify, or delete files on the server
- Start, stop, or restart any service
- Run database migrations or write to databases
- Create, modify, or remove system users
- Modify firewall rules or network configuration

**If a write operation is needed**: describe what you want to do, explain why, and WAIT for explicit "yes" from the user.

### 2. SSH Connection Failures

**STOP on first SSH error.** Do NOT retry.

Production servers use fail2ban. Repeated failed attempts will ban the IP address.
If SSH fails:
1. Report the exact error to the user
2. Do NOT attempt alternative connections
3. Wait for user guidance

### 3. Database Migrations / Schema Changes

**ALWAYS apply migrations to ALL project databases.** Projects may use multiple databases (primary, analytics, secondary services, etc.).

Verify which databases exist and run migrations for each one.

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

---

## Working Principles

The rules above are procedural ("do X"). These are judgment principles — they govern the cases the
rules don't spell out, and each gives a checkable test, not a slogan:

1. **Docs that drift from code are worse than no docs** — wrong docs actively mislead. A change
   isn't done until the docs it affects are fixed (or deleted). Documentation is part of the
   change, not a follow-up.
2. **"Done" means verified by a real request — not "code written."** Exercise the change against
   the running system (an HTTP call, a query, a real webhook) and see the expected result. "It
   should work" and "the command didn't error" are not done.
3. **When unsure, ask — don't assume.** A wrong assumption baked silently into code or config costs
   far more than a question. If a requirement, name, or contract is ambiguous, surface it and wait.

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

- Read env vars via your framework's recommended method (e.g., `decouple.config()` for Python, `process.env` with dotenv for Node, `os.Getenv` for Go)
- All secrets go in `.env` (listed in `.gitignore`) or a secrets manager
- Never hardcode secrets in code or documentation

### Database Setup

<!-- Customize for your project -->
| Alias | Database Name | Purpose |
|-------|--------------|---------|
| `primary` | `{{DB_NAME}}` | Main application database |
<!-- Add more databases as needed -->

### Key Integrations

<!-- List external services your project integrates with -->
<!-- Examples:
- **PostgreSQL / MySQL / MongoDB**: Primary data store
- **Redis / Memcached**: Cache and/or message broker
- **Stripe / PayPal**: Payment processing
- **Telegram / Slack**: Alert notifications
- **S3 / GCS**: File storage
- **BigQuery / Snowflake**: Analytics
-->

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

Two access modes exist for production servers. See `docs/AGENT_SERVER_ACCESS.md` for full details.

| Mode | User | Access Level | Use Case |
|------|------|-------------|----------|
| Diagnostic | `diag` | Read-only | Log checks, SELECT queries, monitoring |
| Investigation | `{{DEPLOY_USER}}` | Full (with permission) | Restarts, migrations, config changes |

**Default**: Always start with Diagnostic Mode. Escalate only when read-only is insufficient.

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

As shipped, this template sits *at* that ceiling, so a new project starts with no headroom.
That is deliberate: the first real edit should be **deleting** — the stack you don't use, the
access model you don't have, the tables you won't fill in. Adding project specifics on top of
the full template is how the 40 KB version begins.

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
