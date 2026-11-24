# Common Pitfalls — {{PROJECT_NAME}}

> Document known issues and their solutions here as you encounter them.
> This is a living document — update it after resolving any non-obvious problem.

---

## Template

```markdown
### #N — Short Description

**Symptom**: What you see when the problem occurs
**Root Cause**: Why it happens
**Fix**: How to resolve it
**Prevention**: How to avoid it in the future
```

---

## Pitfalls

### #1 — Non-ASCII Characters in Config Files

**Symptom**: Systemd service fails to start, encoding errors in logs
**Root Cause**: Russian/Chinese comments in `.env`, `.service`, or `.sh` files
**Fix**: Replace all non-ASCII characters with English equivalents
**Prevention**: ALWAYS use English-only (ASCII) comments in configuration files

### #2 — Timezone Mismatch

**Symptom**: Celery Beat tasks run at wrong times, log timestamps don't match
**Root Cause**: Timezone mismatch between Django settings, Celery Beat, database, and server
**Fix**: Ensure all components use the same timezone (configured in `.env`)
**Prevention**: Set `TIME_ZONE` in `.env` and verify it's used consistently

### #3 — Missing a Migration Target

**Symptom**: New model fields missing, migration errors on secondary databases
**Root Cause**: The migration ran against the default database while the model is routed to a different alias.
**Fix**: Confirm which alias owns the model. For Django, apply the approved migration with `python manage.py migrate --database=<ALIAS>` and verify it with `showmigrations --database=<ALIAS>`.
**Prevention**: Check the [migration targets](../AGENTS.md#3-database-migrations--schema-changes) during deployment.

### #4 — Static Files in Wrong Directory

**Symptom**: Static files not served, 404 errors on CSS/JS
**Root Cause**: Placing static files in `project_config/static/` instead of project root `static/`
**Fix**: Move files to project root `static/` and run `collectstatic`
**Prevention**: Always use project-level `static/` directory

### #5 — SSH Retries Causing IP Ban

**Symptom**: SSH stops accepting connections from the client after several failed logins.
**Root Cause**: fail2ban banned the IP after multiple failed SSH attempts
**Fix**: Check the username and key. If a ban is confirmed, wait for it to expire or contact the host administrator.
**Prevention**: Stop on authentication failures. Use [bounded retries](../AGENTS.md#2-ssh-connection-failures) for expected downtime during an approved reboot.

<!-- Add more pitfalls as you encounter them -->

---

**Last Updated**: {{DATE}}
