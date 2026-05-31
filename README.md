# {{PROJECT_NAME}} — New Project Template

> Framework-agnostic template with agent instructions, deployment configs, and documentation structure.
> Works with any stack: Python, Node.js, Go, Rust, etc.

---

## Quick Start

### 1. Replace Placeholders

Search and replace all `{{PLACEHOLDER}}` values across the project:

| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{{PROJECT_NAME}}` | `My App` | Human-readable project name |
| `{{PROJECT}}` | `myapp` | Machine-friendly project name |
| `{{DOMAIN}}` | `app.example.com` | Production domain |
| `{{SERVER_HOST}}` | `server.example.com` | Server hostname/IP |
| `{{TIMEZONE}}` | `America/New_York` | Project timezone |
| `{{DB_ENGINE}}` | `postgres` | Database engine |
| `{{DB_NAME}}` | `myapp_db` | Database name |
| `{{DB_USER}}` | `myapp_user` | Database username |
| `{{DEPLOY_USER}}` | `deployer` | Linux user for deployments |
| `{{DEPLOY_KEY_NAME}}` | `server-deployer` | SSH key name for deployer |
| `{{DIAG_KEY_NAME}}` | `server-diag` | SSH key name for diagnostic user |
| `{{APP_PATH}}` | `/home/deployer/myapp` | Application path on server |
| `{{APP_LOG_PATH}}` | `/home/deployer/myapp/logs` | Log directory on server |
| `{{APP_PORT}}` | `8000` | Application listen port |
| `{{SERVICE_NAME}}` | `myapp` | Systemd service name |
| `{{WORKER_SERVICE}}` | `myapp-worker` | Background worker service |
| `{{SCHEDULER_SERVICE}}` | `myapp-scheduler` | Task scheduler service |
| `{{NGINX_LOG_PREFIX}}` | `myapp` | Nginx log file prefix |
| `{{BACKUP_PATH}}` | `/mnt/backups` | Backup storage path |
| `{{BROKER_URL}}` | `redis://localhost:6379/0` | Message broker URL |
| `{{RESULT_BACKEND}}` | `redis://localhost:6379/0` | Task result backend |
| `{{QUEUE_NAME}}` | `default` | Task queue name |
| `{{PROCESS_PATTERN}}` | `node\|python\|myapp` | grep pattern for processes |
| `{{PORT_PATTERN}}` | `8000\|5432\|6379` | grep pattern for ports |
| `{{TEST_COMMAND}}` | `pytest tests/ -v` | Run all tests |
| `{{TEST_COMMAND_SPECIFIC}}` | `pytest tests/test_api.py -v` | Run single file |
| `{{TEST_COMMAND_COVERAGE}}` | `pytest tests/ --cov=app -v` | Tests + coverage |
| `{{TEST_PREFIX}}` | `APP_ENV=test` | Env prefix for tests |
| `{{COVERAGE_TARGET}}` | `80` | Minimum coverage % |
| `{{DATE}}` | `2026-03-09` | Current date |
| `{{ANY_TABLE}}` | `users` | Any table name for verification |

### 2. Project Structure

```
├── AGENTS.md                             # Master agent instructions
├── CLAUDE.md -> AGENTS.md                # Symlink for Claude Code
├── GEMINI.md -> AGENTS.md                # Symlink for Gemini / Cursor
├── CHANGELOG.md                          # Change history
├── README.md                             # This file
├── .env.example                          # Environment variables template
├── .gitignore                            # Multi-language gitignore
├── .github/workflows/
│   ├── deploy-initial.yml                # First-time deployment
│   └── deploy-update.yml                 # Automated updates on push
├── deployment/
│   ├── nginx/
│   │   └── app.conf.template             # Reverse proxy with SSL
│   └── systemd/
│       ├── app.service.template          # Application server
│       ├── worker.service.template       # Background worker
│       └── scheduler.service.template    # Task scheduler
└── docs/
    ├── ARCHITECTURE.md                   # Living system specification
    ├── decisions/                        # Architecture Decision Records (ADRs)
    │   ├── README.md                     # ADR convention
    │   └── 0000-adr-template.md          # Copy-me ADR template
    ├── AGENT_SERVER_ACCESS.md            # Diagnostic vs Investigation mode
    ├── API_REFERENCE.md                  # API documentation
    ├── BACKGROUND_TASKS.md               # Task queue / scheduler guide
    ├── COMMON_PITFALLS.md                # Known issues & solutions
    ├── DEPLOYMENT_GUIDE.md               # CI/CD and deployment
    ├── DIAG_USER_SETUP.md                # Read-only diagnostic user runbook
    ├── ENV_VARIABLES.md                  # Environment variables reference
    ├── PRODUCTION_OPERATIONS.md          # Server operations reference
    └── TESTING.md                        # Test structure and conventions
```

### 3. Key Concepts

#### Agent Access Model (Two-Mode System)

AI agents get production access through two isolated users:

- **`diag`** (Diagnostic Mode): Read-only. Separate SSH key. Can read logs, run SELECT queries, check service status. Cannot modify anything.
- **`{{DEPLOY_USER}}`** (Investigation Mode): Full access. Every write operation requires explicit user permission before the agent acts.

See `docs/AGENT_SERVER_ACCESS.md` and `docs/DIAG_USER_SETUP.md`.

#### Configuration Hierarchy

| Layer | Source | Purpose |
|-------|--------|---------|
| 1 | `.env` / secrets manager | Secrets and credentials |
| 2 | Database / config store | Business logic, feature flags |
| 3 | Runtime | One-time overrides, CLI flags |

#### Documentation as Code

All documentation is living — updated with every code change. `AGENTS.md` is the single source of truth for AI agents, propagated via symlinks to `CLAUDE.md` and `GEMINI.md`.

Three documents play distinct roles, and keeping them distinct keeps each one clean:

- **`README.md`** — a concise overview that links out. Not a kitchen sink.
- **`docs/ARCHITECTURE.md`** — the living specification: what the system *is* and is made of.
- **`docs/decisions/`** — ADRs recording *why* significant decisions were made, so the spec and README don't carry that weight.

Per-iteration specs, plans, and checkpoints live in the gitignored `.context/` directory, never in the repo.

---

## Setup Checklist

- [ ] Replace all `{{PLACEHOLDER}}` values
- [ ] Initialize application project
- [ ] Configure `.env` from `.env.example`
- [ ] Set up database(s)
- [ ] Configure GitHub Secrets for CI/CD
- [ ] Generate SSH key pair for `diag` user
- [ ] Run diagnostic user setup (`docs/DIAG_USER_SETUP.md`)
- [ ] Customize deployment workflows
- [ ] Delete files not relevant to your stack
- [ ] Remove this checklist
