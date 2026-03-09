# Production Operations — {{PROJECT_NAME}}

---

## Service Management

```bash
# Systemd
sudo systemctl start|stop|restart {{SERVICE_NAME}}

# Docker Compose
# docker compose up -d / docker compose down / docker compose restart

# PM2 (Node.js)
# pm2 start|stop|restart {{SERVICE_NAME}}
```

### Status Check

```bash
systemctl status {{SERVICE_NAME}} --no-pager
# docker compose ps
# pm2 status
```

---

## Log Management

### Log Locations

| Log | Path | Content |
|-----|------|---------|
| Application | `{{APP_LOG_PATH}}/app.log` | Application errors, warnings |
| Worker | `{{APP_LOG_PATH}}/worker.log` | Background task execution |
| Error | `{{APP_LOG_PATH}}/error.log` | Critical errors |
| Access | `{{APP_LOG_PATH}}/access.log` | HTTP requests |
| Reverse Proxy | `/var/log/nginx/{{NGINX_LOG_PREFIX}}-*.log` | Proxy layer |

### Log Rotation

- Configured via logrotate (or Docker log driver)
- Retention: 30 days
- Max size: 500MB per file

### Common Log Analysis

```bash
# Recent errors
grep -i "error\|traceback\|exception\|panic\|fatal" {{APP_LOG_PATH}}/app.log | tail -30

# 5xx errors in reverse proxy
grep " 50[0-9] " /var/log/nginx/{{NGINX_LOG_PREFIX}}-access.log | tail -20

# Follow in real-time
tail -f {{APP_LOG_PATH}}/app.log
```

---

## Database Operations

### Backups

```bash
# PostgreSQL
pg_dump -U {{DB_USER}} {{DB_NAME}} | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# MySQL
# mysqldump -u {{DB_USER}} -p {{DB_NAME}} | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# MongoDB
# mongodump --db {{DB_NAME}} --archive=backup_$(date +%Y%m%d_%H%M%S).gz --gzip

# List backups
ls -lh {{BACKUP_PATH}}/
```

### Monitoring

```bash
# PostgreSQL — connection count
psql -h localhost -U {{DB_USER}} -d {{DB_NAME}} -c "SELECT count(*) FROM pg_stat_activity;"

# PostgreSQL — database size
psql -h localhost -U {{DB_USER}} -d {{DB_NAME}} -c "SELECT pg_size_pretty(pg_database_size('{{DB_NAME}}'));"

# PostgreSQL — slow queries
psql -h localhost -U {{DB_USER}} -d {{DB_NAME}} -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;
"
```

---

## Monitoring Checklist

Daily (or automated):
- [ ] All services running
- [ ] No disk space issues (`df -h`)
- [ ] No error spikes in logs
- [ ] Health endpoint responds
- [ ] Background tasks executing on schedule

Weekly:
- [ ] Database backup verification
- [ ] Log rotation working
- [ ] SSL certificate expiration check

---

**Last Updated**: {{DATE}}
