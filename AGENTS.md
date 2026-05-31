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

New features MUST NOT break application startup or core functionality. Always verify the app starts correctly after changes.

### 7. External Service Dependencies

When adding integrations with external services, match production patterns:
- Authentication method (API keys, OAuth, HMAC)
- Port and protocol requirements
- Rate limiting configuration
- Error handling and retry logic

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
| Any change | `CHANGELOG.md` + "Latest Updates" section below |

> **Per-iteration specs, plans, and checkpoints live in the gitignored `.context/`, not in the
> repo.** The committed docs describe what the system *is*; `.context/` holds the working notes for
> how it's being changed right now.

---

## Documentation Map

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Master agent instructions (this file) |
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

## Operations Quick Reference

### Health Check
```bash
# Application health
curl -s https://{{DOMAIN}}/health | python3 -m json.tool

# Service status (systemd)
systemctl status {{SERVICE_NAME}} --no-pager

# Service status (Docker)
docker compose ps

# Disk usage
df -h /
```

### Common Troubleshooting

See `docs/COMMON_PITFALLS.md` for documented issues and solutions.

### Log Locations

```bash
# Application logs
{{LOG_PATH}}/app.log              # Application errors
{{LOG_PATH}}/worker.log           # Background task execution

# System logs (systemd)
journalctl -u {{SERVICE_NAME}} -n 100 --no-pager

# Container logs (Docker)
docker compose logs --tail=100 {{SERVICE_NAME}}
```

---

## Latest Updates

<!-- Keep the 3 most recent entries here. Full history in CHANGELOG.md -->

1. **{{DATE}}** — Initial project setup
