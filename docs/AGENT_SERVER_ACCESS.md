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

**User**: `diag` — read-only diagnostics. The sole sudo delegation runs the PostgreSQL dispatcher as its unprivileged service account.
**Database role**: `diagnostic_user` — SELECT-only on configured project databases, with server-side limits, reached through
the `diag-sql` wrapper.

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

Every query goes through the `diag-sql` wrapper (`docs/DIAG_USER_SETUP.md`, section 6b), one query per call. Never
run the database client directly, over ssh or otherwise: the wrapper is what applies the time and resource limits.

```bash
ssh -i ~/.ssh/{{DIAG_KEY_NAME}} diag@{{SERVER_HOST}} diag-sql < query.sql
# For a second configured database, pass its name explicitly.
ssh -i ~/.ssh/{{DIAG_KEY_NAME}} diag@{{SERVER_HOST}} diag-sql {{DB_NAME}} < query.sql
```

**Query rules.** A read-only query can still overload the database for everyone:

- Filter on indexed columns, by an exact value or a prefix (`LIKE 'abc%'`). No leading-wildcard `LIKE`, no regex,
  no cast of a JSON or text column to search inside it across a table. Extract JSON keys with `->>`.
- Bound every query on a large table by a time window on an indexed column. Start with one day and widen only
  when the answer needs it.
- `LIMIT` every query that does not aggregate. Ask one question per query and keep the query next to its output.
- Check the plan with `EXPLAIN` when unsure. Not `EXPLAIN ANALYZE`: it runs the query.
- Columnar engines (ClickHouse and similar): always filter on the partition or time key; no `FINAL` and no exact
  distinct counts on large tables. Use approximate counts, and collapse rows in the query instead of `FINAL`.
- A query that really needs a full scan is written down and handed to the user, who decides whether to run it
  off-peak or add an index.
- A refusal from the wrapper or a hit limit is a boundary: rewrite the query, do not look for a way around it.

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
ORDER BY query_start DESC LIMIT 20;

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
- Use administrative sudo. The diagnostic dispatcher is the only delegated command.
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
3. **SSH failures** — check credentials after an authentication failure. During an approved reboot, use the bounded reconnect procedure in [the project rules](../AGENTS.md#2-ssh-connection-failures).
4. **Infrastructure operations** — provide step-by-step instructions, let user execute
5. **Approved means that change only** — write the steps down before asking (host, file, exact change, how to
   check it). After the yes, run exactly those steps. A check or fix you think of on the way goes back to the user
   first. If a precondition is not met, stop and report.
6. **Database reads still go through `diag-sql`**, also while you hold this access.

### Available Actions (read-only, no permission needed)

Everything from Diagnostic Mode, plus:

```bash
# Application CLI / management commands (read-only)
cd {{APP_PATH}}
# Activate environment (virtualenv, nvm, etc.) if needed

# Inspect service state and the location of its configuration
systemctl show {{SERVICE_NAME}} -p ActiveState -p SubState
systemctl show {{SERVICE_NAME}} -p FragmentPath
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
echo "SELECT datname, numbackends, xact_commit, xact_rollback, deadlocks
      FROM pg_stat_database WHERE datname = '{{DB_NAME}}';" \
  | ssh -i ~/.ssh/{{DIAG_KEY_NAME}} diag@{{SERVER_HOST}} diag-sql
```

### "Disk space issue?"
```bash
df -h /
du -sh {{APP_LOG_PATH}}/*.log | sort -rh | head -10
```

---

**Last Updated**: {{DATE}}
