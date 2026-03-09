# Background Tasks — {{PROJECT_NAME}}

---

## Architecture

Background tasks handle work that shouldn't block HTTP requests: sending emails, processing webhooks, scheduled jobs, data sync, etc.

### Common Task Queue Options

| Tool | Language | Broker | Use Case |
|------|----------|--------|----------|
| Celery | Python | Redis, RabbitMQ | Full-featured, periodic tasks |
| Bull / BullMQ | Node.js | Redis | Queue management with UI |
| Sidekiq | Ruby | Redis | High-performance |
| Asynq | Go | Redis | Simple, reliable |
| Custom | Any | Redis, DB | Simple queue needs |

---

## Configuration

| Setting | Value | Source |
|---------|-------|--------|
| Broker | `{{BROKER_URL}}` | `.env` → `BROKER_URL` |
| Result Backend | `{{RESULT_BACKEND}}` | `.env` → `RESULT_BACKEND` |
| Timezone | `{{TIMEZONE}}` | `.env` → `TIME_ZONE` |

**CRITICAL**: Task scheduler timezone MUST match the application timezone. Never use UTC if the project uses a local timezone.

---

## Running Locally

```bash
# Start the worker (customize for your stack)
# Celery: celery -A {{PROJECT}} worker -l info
# BullMQ: npm run worker
# Custom: ./worker

# Start the scheduler (if using periodic tasks)
# Celery Beat: celery -A {{PROJECT}} beat -l info
# node-cron: included in worker process
```

---

## Production

```bash
# Service status (systemd)
systemctl status {{WORKER_SERVICE}} --no-pager

# Service status (Docker)
# docker compose ps worker

# Logs
journalctl -u {{WORKER_SERVICE}} -n 100 --no-pager
tail -f {{APP_LOG_PATH}}/worker.log

# Restart (requires explicit user permission)
sudo systemctl restart {{WORKER_SERVICE}}
```

---

## Queue Management

```bash
# Check queue length (Redis)
redis-cli -n 0 LLEN {{QUEUE_NAME}}

# Inspect active/waiting tasks (Celery example)
# celery -A {{PROJECT}} inspect active
# celery -A {{PROJECT}} inspect reserved

# Purge queue (DESTRUCTIVE — ask user first)
# celery -A {{PROJECT}} purge
# redis-cli -n 0 DEL {{QUEUE_NAME}}
```

---

## Troubleshooting

### Tasks Not Executing

1. Check worker process is running
2. Check broker connectivity (e.g., `redis-cli PING`)
3. Check queue length — tasks may be piling up
4. Check worker logs for errors

### Tasks Running at Wrong Time

1. Verify timezone configuration matches across app, scheduler, and server
2. Check scheduled task configuration in DB or config file
3. Restart scheduler after schedule changes

### Worker Memory Issues

1. Check max-tasks-per-child or equivalent setting
2. Monitor with `ps aux | grep worker`
3. Restart worker process

---

**Last Updated**: {{DATE}}
