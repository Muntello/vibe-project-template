# Agent Server Access Guide

Two access modes exist for working with the production server. Choose the appropriate mode based on the task.

**Server**: {{SERVER_HOST}}
**Timezone**: {{TIMEZONE}}

---

## Mode Selection

| Question | Diagnostic Mode | Investigation Mode |
|----------|----------------|-------------------|
| Need to restart services? | No | Yes |
| Need to modify files/config? | No | Yes |
| Need to write to databases? | No | Yes |
| Need to run migrations? | No | Yes |
| Need to install software? | No | Yes |
| Routine log checks or monitoring? | **Yes** | Overkill |
| Checking why something failed? | **Start here** | Escalate if needed |
| Running SELECT queries for analysis? | **Yes** | Not needed |

**Default**: Always start with Diagnostic Mode. Escalate to Investigation Mode only when read-only access is insufficient.

---

## Mode 1: Diagnostic Mode (Read-Only)

**SSH Connection:**
```bash
ssh -i ~/.ssh/{{DIAG_KEY_NAME}} diag@{{SERVER_HOST}}
```

**User**: `diag` — no sudo, read-only access only.
**Database role**: `diagnostic_user` — SELECT-only on all project databases.

### Available Actions

#### Logs

```bash
# Application logs
tail -200 {{APP_LOG_PATH}}/app.log
tail -200 {{APP_LOG_PATH}}/worker.log
tail -200 {{APP_LOG_PATH}}/error.log

# Follow in real-time
tail -f {{APP_LOG_PATH}}/app.log

# Search for errors
grep -i "error\|traceback\|exception\|panic\|fatal" {{APP_LOG_PATH}}/app.log | tail -50

# Search by date
grep "YYYY-MM-DD" {{APP_LOG_PATH}}/app.log | grep -i error

# System logs (systemd)
journalctl -u {{SERVICE_NAME}} -n 100 --no-pager
journalctl -u {{SERVICE_NAME}} --since "1 hour ago" --no-pager

# Container logs (Docker)
# docker compose logs --tail=200 {{SERVICE_NAME}}

# Reverse proxy logs
tail -200 /var/log/nginx/{{NGINX_LOG_PREFIX}}-access.log
tail -200 /var/log/nginx/{{NGINX_LOG_PREFIX}}-error.log
```

#### Service Status

```bash
# Systemd services
systemctl status {{SERVICE_NAME}} --no-pager

# Docker containers
# docker compose ps

# Process check
ps aux | grep -E "{{PROCESS_PATTERN}}" | grep -v grep
```

#### Database Queries (SELECT Only)

```bash
# PostgreSQL
psql -h localhost -U diagnostic_user -d {{DB_NAME}}

# MySQL
# mysql -h localhost -u diagnostic_user -p {{DB_NAME}}

# MongoDB (read-only role)
# mongosh --host localhost -u diagnostic_user -p --authenticationDatabase admin {{DB_NAME}}
```

**Useful diagnostic queries (PostgreSQL):**

```sql
-- Table sizes
SELECT relname, pg_size_pretty(pg_relation_size(oid))
FROM pg_class
WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace
ORDER BY pg_relation_size(oid) DESC LIMIT 20;

-- Active connections
SELECT datname, usename, state, query_start, query
FROM pg_stat_activity
WHERE datname = '{{DB_NAME}}'
ORDER BY query_start DESC;

-- Database health
SELECT datname, numbackends, xact_commit, xact_rollback, deadlocks
FROM pg_stat_database WHERE datname = '{{DB_NAME}}';
```

#### System Health

```bash
# Disk usage
df -h /

# Log directory sizes
du -sh {{APP_LOG_PATH}}/*.log | sort -rh

# Memory / CPU
free -h
uptime

# Network
ss -tlnp | grep -E "{{PORT_PATTERN}}"
```

### Restrictions in Diagnostic Mode

**You CANNOT and MUST NOT attempt to:**
- Run `sudo` anything — it will be denied
- Modify or delete files
- Restart services
- Run application CLI commands (no access to app runtime)
- Access `.env` or any secrets
- Write to databases (INSERT, UPDATE, DELETE)
- Install or remove software

**If you need any of the above**: Tell the user you need to escalate to Investigation Mode and explain why.

---

## Mode 2: Investigation Mode (Full Access)

**SSH Connection:**
```bash
ssh -i ~/.ssh/{{DEPLOY_KEY_NAME}} {{DEPLOY_USER}}@{{SERVER_HOST}}
```

**User**: `{{DEPLOY_USER}}` — sudo access available, full project access.

### Critical Rules

**ALL rules from AGENTS.md "Critical Production Rules" section apply in full.** Key reminders:

1. **READ-ONLY by default** — all write operations require explicit user permission
2. **Ask before acting** — "Should I [action] on production?" and wait for "yes"
3. **SSH failure = STOP** — on first SSH error, stop all attempts immediately (fail2ban risk)
4. **Infrastructure operations** — provide step-by-step instructions, let user execute

### Available Actions (read-only, no permission needed)

Everything from Diagnostic Mode, plus:

```bash
# Application CLI / management commands (read-only)
cd {{APP_PATH}}
# Activate environment (virtualenv, nvm, etc.) if needed

# Read configuration
cat {{APP_PATH}}/.env
cat /etc/systemd/system/{{SERVICE_NAME}}.service
# cat {{APP_PATH}}/docker-compose.yml

# Cache/broker inspection
# redis-cli INFO
# redis-cli DBSIZE
```

### Actions Requiring Explicit User Permission

| Action | Ask User First |
|--------|---------------|
| Restart application services | YES |
| Run database migrations | YES |
| Modify `.env` or config files | YES |
| Write to database | YES |
| Deploy code changes | YES |
| Modify reverse proxy config | YES |
| Install packages or dependencies | YES |

---

## Escalation Protocol

When working in Diagnostic Mode and finding that you need write access:

1. **Document what you found** — describe the issue based on diagnostic data
2. **Explain why escalation is needed** — what specific action requires Investigation Mode
3. **Ask the user** — "I need to escalate to Investigation Mode to [specific action]. Should I proceed?"
4. **Wait for explicit confirmation** before switching modes

---

## Quick Reference: Diagnostic Queries by Scenario

### "Is the app working?"
```bash
curl -s https://{{DOMAIN}}/health | python3 -m json.tool
systemctl status {{SERVICE_NAME}} --no-pager
df -h /
```

### "Why are requests failing?"
```bash
grep -i "error\|traceback\|500" {{APP_LOG_PATH}}/app.log | tail -30
grep " 500 " /var/log/nginx/{{NGINX_LOG_PREFIX}}-access.log | tail -20
```

### "Is the database healthy?"
```bash
psql -h localhost -U diagnostic_user -d {{DB_NAME}} -c "
  SELECT datname, numbackends, xact_commit, xact_rollback, deadlocks
  FROM pg_stat_database WHERE datname = '{{DB_NAME}}';
"
```

### "Disk space issue?"
```bash
df -h /
du -sh {{APP_LOG_PATH}}/*.log | sort -rh | head -10
```

---

**Last Updated**: {{DATE}}
