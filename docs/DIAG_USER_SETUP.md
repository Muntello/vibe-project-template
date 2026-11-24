# Diagnostic User Setup Runbook

**Purpose**: Create a restricted Linux user `diag` with SSH key access for read-only diagnostics (log viewing, database SELECT queries, service status checks). No administrative sudo or production writes. The PostgreSQL setup delegates one read-only command to a service account.

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

For a new installation, create the dedicated role below. On an upgrade, verify its existing grants and continue with the resource limits and authentication changes in steps 6a and 6b.

```bash
# Create the role
sudo -u postgres psql -c "CREATE ROLE diagnostic_user LOGIN;"

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

For PostgreSQL, verify the SQL role and its limits through the installed dispatcher in step 9. For MySQL and MongoDB, a read-only grant alone does not provide the bounded diagnostic endpoint.

## 6a. Limit What One Query Can Cost

Read-only does not mean harmless. A single SELECT with a leading-wildcard search, a regex or an exact distinct count
over a large table can hold the database CPU or memory for minutes and take the application down with it. Give the
diagnostic role limits that the server enforces, sized so that one runaway query still leaves the application
enough CPU and memory on the smallest machine that runs this database.

### PostgreSQL

```bash
sudo -u postgres psql <<'SQL'
ALTER ROLE diagnostic_user SET default_transaction_read_only = on;
ALTER ROLE diagnostic_user SET statement_timeout = '8s';
ALTER ROLE diagnostic_user SET lock_timeout = '2s';
ALTER ROLE diagnostic_user SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE diagnostic_user CONNECTION LIMIT 3;
SQL
```

The timeout settings are session defaults. Step 6b gives the database identity to a separate OS account and starts a fresh read-only transaction for each diagnostic request. The connection cap and timeouts limit concurrency and elapsed statement time. Size memory and temporary-file budgets separately for the deployment.

### MySQL

```sql
ALTER USER 'diagnostic_user'@'localhost' WITH MAX_USER_CONNECTIONS 3 MAX_QUERIES_PER_HOUR 600;
```

These settings cap connection and request counts. A MySQL-specific dispatcher must also set and verify the session's `max_execution_time` before exposing the role to agents. The PostgreSQL dispatcher below supports PostgreSQL only.

### ClickHouse

```sql
CREATE USER IF NOT EXISTS diagnostic_user IDENTIFIED WITH sha256_password BY 'GENERATE_PASSWORD_HERE';
CREATE SETTINGS PROFILE IF NOT EXISTS diag_limits TO diagnostic_user;
ALTER SETTINGS PROFILE diag_limits SETTINGS
    readonly = 1,
    max_execution_time = 8,
    max_memory_usage = 500000000,
    max_rows_to_read = 30000000,
    max_bytes_to_read = 3000000000,
    max_threads = 2
    TO diagnostic_user;
GRANT SELECT ON {{DB_NAME}}.* TO diagnostic_user;
```

Reserve this profile for the diagnostic account. The `ALTER` step also updates an existing profile and assigns it to an existing user. In a fresh diagnostic session, check the effective values of the settings above in `system.settings` before enabling access.

`readonly = 1` also forbids changing settings, including a `SETTINGS` clause in the query, so these limits are hard.
Needs SQL-driven access control on the server (`access_management` enabled for the admin user).

## 6b. Install the Query Wrapper

The [PostgreSQL dispatcher](../deployment/diagnostics/diag-sql.py) accepts one SELECT or plain EXPLAIN on stdin. Its read-only transaction, statement timeout and rollback are separate from the submitted SQL. It returns CSV. Query-shape checks catch common mistakes; a valid SELECT can still be expensive. Use a read replica or separate resource controls when a shared server needs stronger workload isolation.

Run the following as an administrator from the repository root. The example targets Debian/Ubuntu with Python 3, the venv module, sudo and a local PostgreSQL server. Create a locked OS service account named `diagnostic_user` with no interactive login. On an existing installation, reuse it only if it is already dedicated to this dispatcher.

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin diagnostic_user
sudo install -d -o root -g root -m 0755 /usr/local/libexec /etc/diag-sql
sudo python3 -m venv /opt/diag-sql
sudo /opt/diag-sql/bin/pip install 'psycopg[binary]>=3.2,<4' 'pglast>=7,<8'
sudo install -o root -g root -m 0755 deployment/diagnostics/diag-sql.py /usr/local/libexec/diag-sql
sudoedit /etc/diag-sql/databases
sudo chown root:root /etc/diag-sql/databases
sudo chmod 0644 /etc/diag-sql/databases
```

List every permitted database in the root-owned `/etc/diag-sql/databases`, one name per line. The first is the default. Use an explicit name for another target. Configure local **peer** authentication for this PostgreSQL role on the Unix socket. Put the following rule before broader matching rules in `pg_hba.conf`, and reload PostgreSQL after validating the configuration.

```text
local   all   diagnostic_user   peer
```

Keep the role exclusive to the dispatcher. On upgrades, remove password authentication for the dedicated role and retire its old password files after checking existing consumers. Check for additional authentication or role memberships that would still give the interactive `diag` account direct access.

```bash
sudo -u postgres psql -c "ALTER ROLE diagnostic_user PASSWORD NULL"
```

Use `visudo -f /etc/sudoers.d/diag-sql` to grant just this executable as the unprivileged service account. The dispatcher validates the database argument against its allowlist. Keep the executable, its dependencies, the allowlist and their parent directories administrator-owned.

```text
diag ALL=(diagnostic_user) NOPASSWD: NOSETENV: /usr/local/libexec/diag-sql
```

Install the entry point used by diagnostic SSH sessions.

```bash
sudo tee /usr/local/bin/diag-sql >/dev/null <<'WRAPPER'
#!/bin/sh
exec /usr/bin/sudo -n -u diagnostic_user -- /usr/local/libexec/diag-sql "$@"
WRAPPER
sudo chown root:root /usr/local/bin/diag-sql
sudo chmod 0755 /usr/local/bin/diag-sql
```

```bash
ssh -i ~/.ssh/{{DIAG_KEY_NAME}} diag@{{SERVER_HOST}} diag-sql < query.sql
ssh -i ~/.ssh/{{DIAG_KEY_NAME}} diag@{{SERVER_HOST}} diag-sql {{DB_NAME}} < query.sql
```

## 7. Other database engines

For MySQL, ClickHouse or MongoDB, install and verify an engine-specific dispatcher before enabling agent reads. Keep its database credentials with the service account. Test its single-request deadline, resource limits and read-only grants using the same entry point the agent will use.

For changes to the supplied PostgreSQL code, run `python tests/test_diagnostic_access.py` with the dispatcher dependencies installed. Set `DIAG_TEST_DSN` to a disposable PostgreSQL database to include the transaction, delimiter and timeout tests.

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
alias db='diag-sql'

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
sudo -l                                                                        # -> only the diagnostic dispatcher
echo "SELECT 1 LIMIT 1" | diag-sql                                             # -> one row, no semicolon needed
echo "SELECT current_database();" | diag-sql {{DB_NAME}}                       # -> selected database
echo "SELECT pg_sleep(20)" | diag-sql                                          # -> canceled by statement timeout
echo "SELECT * FROM {{ANY_TABLE}} WHERE name ILIKE '%x%'" | diag-sql            # -> refused
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
| SELECT from configured databases | `diag-sql [database]` with the limits of 6a |
| Check disk usage | `df -h`, `du` |
| Check processes | `ps aux`, `top`, `htop` |
| Network diagnostics | `ss`, `ping` |

### What diag User CANNOT Do

| Action | Why |
|--------|-----|
| Modify/delete files | No write permissions via ACL |
| Restart services | No administrative sudo |
| Install software | No administrative sudo |
| Modify databases | No INSERT/UPDATE/DELETE grants |
| Read `.env` secrets | No access to app user's non-log files |
| Modify server config | No administrative sudo, no write perms |

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
