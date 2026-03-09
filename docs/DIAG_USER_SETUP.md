# Diagnostic User Setup Runbook

**Purpose**: Create a restricted Linux user `diag` with SSH key access for read-only diagnostics (log viewing, database SELECT queries, service status checks). No sudo, no write access.

**Server**: {{SERVER_HOST}}

---

## Why a Separate Diagnostic User?

AI agents (Claude Code, Cursor, etc.) need production access for troubleshooting but should NEVER have write access by default. The `diag` user provides:

- **Least-privilege access** — only SELECT queries, log reading, service status
- **Audit trail** — all diag activity is logged under a separate user
- **Safety** — cannot accidentally modify data, restart services, or break configs
- **Separate SSH key** — can be revoked independently without affecting deployments

---

## 1. Create Linux User

```bash
sudo adduser --disabled-password --gecos "Diagnostic read-only user" diag

# IMPORTANT: --disabled-password leaves the account locked, which blocks SSH key auth.
# Unlock by setting an invalid password (login by password remains impossible):
sudo usermod -p '*' diag
```

## 2. Set Up SSH Key Authentication

The public key will be provided by the user who generated the keypair on their machine.

```bash
sudo mkdir -p /home/diag/.ssh
echo "PASTE_PUBLIC_KEY_HERE" | sudo tee /home/diag/.ssh/authorized_keys
sudo chmod 700 /home/diag/.ssh
sudo chmod 600 /home/diag/.ssh/authorized_keys
sudo chown -R diag:diag /home/diag/.ssh
```

## 3. Grant Read Access to Application Logs

```bash
# Add diag to the app user's group so it can traverse the app directory
sudo usermod -aG {{DEPLOY_USER}} diag

# Set ACLs on log directory (read + traverse, recursive)
sudo setfacl -R -m u:diag:rX {{APP_PATH}}/logs/

# Set default ACL so NEW log files also get read access for diag
sudo setfacl -R -d -m u:diag:rX {{APP_PATH}}/logs/

# Allow traversal to reach the logs directory
sudo setfacl -m u:diag:x /home/{{DEPLOY_USER}}
sudo setfacl -m u:diag:x {{APP_PATH}}
```

### Verify log access

```bash
sudo -u diag ls {{APP_PATH}}/logs/
sudo -u diag head -5 {{APP_PATH}}/logs/app.log
```

## 4. Grant Access to System Logs (journalctl)

```bash
sudo usermod -aG systemd-journal diag
```

## 5. Grant Access to Reverse Proxy Logs (optional)

```bash
# Nginx logs are at /var/log/nginx/ owned by root:adm
sudo usermod -aG adm diag
```

## 6. Create Read-Only Database Role

### PostgreSQL

```bash
# Create the role
sudo -u postgres psql -c "CREATE ROLE diagnostic_user WITH LOGIN PASSWORD 'GENERATE_PASSWORD_HERE';"

# Grant on each database — repeat for every project database
sudo -u postgres psql -d {{DB_NAME}} <<'SQL'
GRANT CONNECT ON DATABASE {{DB_NAME}} TO diagnostic_user;
GRANT USAGE ON SCHEMA public TO diagnostic_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO diagnostic_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO diagnostic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO diagnostic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO diagnostic_user;
SQL
```

### MySQL (alternative)

```sql
CREATE USER 'diagnostic_user'@'localhost' IDENTIFIED BY 'GENERATE_PASSWORD_HERE';
GRANT SELECT ON {{DB_NAME}}.* TO 'diagnostic_user'@'localhost';
FLUSH PRIVILEGES;
```

### MongoDB (alternative)

```javascript
db.createUser({
  user: "diagnostic_user",
  pwd: "GENERATE_PASSWORD_HERE",
  roles: [{ role: "read", db: "{{DB_NAME}}" }]
});
```

### Verify database access

```bash
# PostgreSQL
psql -h localhost -U diagnostic_user -d {{DB_NAME}} -c "SELECT 1;"

# Verify write is denied
psql -h localhost -U diagnostic_user -d {{DB_NAME}} -c "DELETE FROM {{ANY_TABLE}} WHERE 1=0;"
# Expected: ERROR: permission denied
```

## 7. Create Credential File for Passwordless CLI Access

### PostgreSQL (.pgpass)

```bash
sudo -u diag bash -c 'cat > /home/diag/.pgpass <<EOF
localhost:5432:{{DB_NAME}}:diagnostic_user:PASSWORD_FROM_STEP_6
EOF'
sudo chmod 600 /home/diag/.pgpass
sudo chown diag:diag /home/diag/.pgpass
```

### MySQL (.my.cnf)

```bash
sudo -u diag bash -c 'cat > /home/diag/.my.cnf <<EOF
[client]
user=diagnostic_user
password=PASSWORD_FROM_STEP_6
EOF'
sudo chmod 600 /home/diag/.my.cnf
sudo chown diag:diag /home/diag/.my.cnf
```

## 8. Add Convenience Aliases (optional)

```bash
sudo -u diag tee /home/diag/.bash_aliases <<'ALIASES'
# Log shortcuts
alias logs='ls -lhS {{APP_PATH}}/logs/*.log'
alias app-log='tail -f {{APP_PATH}}/logs/app.log'
alias error-log='tail -f {{APP_PATH}}/logs/error.log'
alias worker-log='tail -f {{APP_PATH}}/logs/worker.log'

# Service status
alias status-all='systemctl status {{SERVICE_NAME}} --no-pager'

# Database shortcuts (PostgreSQL example)
alias db='psql -h localhost -U diagnostic_user -d {{DB_NAME}}'

# Disk usage
alias disk='df -h /'
ALIASES
```

## 9. Verify Everything

```bash
# From client machine
ssh -i ~/.ssh/{{DIAG_KEY_NAME}} diag@{{SERVER_HOST}}

# Once connected:
whoami                                                                         # -> diag
sudo ls /root                                                                  # -> permission denied
head -5 {{APP_PATH}}/logs/app.log                                              # -> works
systemctl status {{SERVICE_NAME}} --no-pager                                   # -> works
psql -h localhost -U diagnostic_user -d {{DB_NAME}} -c "SELECT 1"             # -> works
psql -h localhost -U diagnostic_user -d {{DB_NAME}} -c "DROP TABLE test"      # -> permission denied
```

---

## Access Summary

### What diag User CAN Do

| Action | How |
|--------|-----|
| Read application logs | `tail`, `grep`, `less` on `{{APP_PATH}}/logs/` |
| Read system logs | `journalctl -u <service>` |
| Read reverse proxy logs | `tail /var/log/nginx/*.log` |
| Check service status | `systemctl status <service>` |
| SELECT from all databases | DB CLI with `diagnostic_user` |
| Check disk usage | `df -h`, `du` |
| Check processes | `ps aux`, `top`, `htop` |
| Network diagnostics | `ss`, `ping` |

### What diag User CANNOT Do

| Action | Why |
|--------|-----|
| Modify/delete files | No write permissions via ACL |
| Restart services | No sudo |
| Install software | No sudo |
| Modify databases | No INSERT/UPDATE/DELETE grants |
| Read `.env` secrets | No access to app user's non-log files |
| Modify server config | No sudo, no write perms |

---

## Revoking Access

```bash
# Disable SSH login (preserves user for audit trail)
sudo usermod --expiredate 1 diag

# OR fully remove user and DB role
sudo deluser --remove-home diag

# PostgreSQL
sudo -u postgres psql -c "
  REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM diagnostic_user;
  REVOKE CONNECT ON DATABASE {{DB_NAME}} FROM diagnostic_user;
  DROP ROLE diagnostic_user;
"

# MySQL
# DROP USER 'diagnostic_user'@'localhost';

# MongoDB
# db.dropUser("diagnostic_user")
```

---

**Password Generation** (run locally):
```bash
openssl rand -base64 32
```

**Last Updated**: {{DATE}}
