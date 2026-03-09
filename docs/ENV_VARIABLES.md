# Environment Variables Reference — {{PROJECT_NAME}}

> Authoritative reference for all environment variables.
> When adding new variables: update this file, app config, AND `.env.example`.

---

## Rules

1. **Never commit `.env`** — it is in `.gitignore`
2. **ASCII-only comments** in `.env` files (no Russian, Chinese, etc.)
3. **Use your framework's recommended method** for reading env vars
4. **Production passwords**: 32+ characters, generated with `openssl rand -base64 32`
5. **Admin passwords**: 12+ characters minimum

---

## Application Core

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | No | `development` | Environment: development, staging, production |
| `APP_SECRET` | Yes | — | Application secret key |
| `APP_PORT` | No | `8000` | Port the application listens on |
| `APP_HOST` | No | `0.0.0.0` | Bind address |
| `LOG_LEVEL` | No | `info` | Logging level |
| `TIME_ZONE` | No | `America/New_York` | Must match server and all services |

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_ENGINE` | Yes | — | Database engine (postgres, mysql, mongodb, sqlite) |
| `DB_NAME` | Yes | — | Database name |
| `DB_USER` | Yes | — | Database username |
| `DB_PASSWORD` | Yes | — | Database password (32+ chars in production) |
| `DB_HOST` | No | `localhost` | Database host |
| `DB_PORT` | No | varies | Database port |
| `DB_CONNECTION_STRING` | No | — | Alternative: full connection string |

## Cache

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CACHE_URL` | No | `redis://localhost:6379/1` | Cache backend URL |

## Message Broker / Task Queue

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BROKER_URL` | No | — | Message broker URL |
| `RESULT_BACKEND` | No | — | Task result backend URL |

## Notifications

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | No | — | Telegram bot token |
| `TELEGRAM_CHAT_ID` | No | — | Telegram chat/group ID |
| `SLACK_WEBHOOK_URL` | No | — | Slack incoming webhook |

## Internal API Keys

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | No | — | Service-to-service auth key (32+ chars) |
| `WEBHOOK_SECRET` | No | — | Webhook signature verification secret |

<!-- Add sections for each external integration as needed -->

---

## Adding New Variables

When adding a new environment variable:

1. Add to application config with a sensible default (where appropriate)
2. Add to `.env.example` with a descriptive comment
3. Add to this file in the appropriate section
4. If it's a secret, ensure `.env` is in `.gitignore`
5. Update `CHANGELOG.md`

---

**Last Updated**: {{DATE}}
