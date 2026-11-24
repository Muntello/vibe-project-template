# Deployment Guide — {{PROJECT_NAME}}

---

## Deployment Architecture

### Users and Roles

| User | Purpose | Access Level |
|------|---------|-------------|
| `{{DEPLOY_USER}}` | Application deployment and management | sudo, full project access |
| `diag` | Agent diagnostic access (read-only) | No sudo, SELECT-only DB, log reading |

### SSH Keys

| Key | User | Purpose |
|-----|------|---------|
| `{{DEPLOY_KEY_NAME}}` | `{{DEPLOY_USER}}` | Deployment and full server access |
| `{{DIAG_KEY_NAME}}` | `diag` | Read-only diagnostic access for agents |

---

## CI/CD (GitHub Actions)

### Required GitHub Secrets

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | `{{SERVER_HOST}}` |
| `DEPLOY_USER` | `{{DEPLOY_USER}}` |
| `DEPLOY_SSH_KEY` | Deploy user's private SSH key |

### Workflow: Initial Deployment

**Trigger**: Manual (`workflow_dispatch`)
**File**: `.github/workflows/deploy-initial.yml`

First-time server setup: creates database, configures services, deploys code.

### Workflow: Code Update

**Trigger**: Push to `main` (auto) or manual
**File**: `.github/workflows/deploy-update.yml`

Steps:
1. Pull latest code
2. Update dependencies
3. Run tests — failures block deployment
4. Identify the database aliases targeted by this release. Apply and verify each migration on its intended targets.
5. Build assets (if applicable)
6. Restart application services
7. Health check — **rollback on failure**

---

## Manual Deployment (Fallback)

```bash
ssh -i ~/.ssh/{{DEPLOY_KEY_NAME}} {{DEPLOY_USER}}@{{SERVER_HOST}}
cd {{APP_PATH}}

# Pull changes
git fetch origin main
git reset --hard origin/main

# Update dependencies (choose your stack)
# Python: pip install -r requirements.txt
# Node.js: npm ci
# Go: go build ./...
# Rust: cargo build --release

# Run migrations for the configured target (if applicable)
# Django: python manage.py migrate --database=<ALIAS>
# Node.js: npx prisma migrate deploy / npx knex migrate:latest
# Go: goose up

# Build assets (if applicable)
# npm run build

# Restart services
# Systemd: sudo systemctl restart {{SERVICE_NAME}}
# Docker: docker compose up -d --build
# PM2: pm2 restart all

# Verify
curl -s https://{{DOMAIN}}/health
```

---

## Post-Deployment Verification

```bash
# Service status
systemctl status {{SERVICE_NAME}} --no-pager
# docker compose ps

# Application health
curl -s https://{{DOMAIN}}/health | python3 -m json.tool

# Recent errors
tail -50 {{APP_PATH}}/logs/app.log | grep -i error

# Disk space
df -h /
```

---

## Rollback

```bash
cd {{APP_PATH}}
git log --oneline -5
git reset --hard HEAD^
# Reinstall dependencies
# Re-run migrations if needed
# Restart services
```

---

**Last Updated**: {{DATE}}
