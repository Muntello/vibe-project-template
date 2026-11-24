#!/usr/bin/env python3
# Claude Code PreToolUse hook for the Bash tool. See .claude/hooks/README.md for installation.
#
# Two guards on the command line the agent is about to run:
# 1. Production databases: refuses a database client run over ssh or pointed at a remote host. Agents read
#    production only through the read-only wrapper on the server (docs/DIAG_USER_SETUP.md), which keeps its
#    limits; `ssh diag@host diag-sql < query.sql` is not affected.
# 2. Credentials: refuses listings of password-manager vaults and items, of the SSH agent's keys, and reads of the
#    macOS keychain. An agent uses the access it was given and asks the user for anything else.
#
# This is a guard against mistakes, not a security boundary: a command hidden in a script the agent wrote is not
# seen. Exit 2 blocks the command and returns the message to the model; input it cannot parse is let through.
import json
import re
import sys

CLIENTS = (r"(psql|pg_dump|pg_dumpall|pg_restore|clickhouse-client|clickhouse\s+client|mysql|mysqldump|mariadb"
           r"|mongo|mongosh|redis-cli|cqlsh|sqlite3)")
LOCAL = r"(localhost|127\.0\.0\.1|::1|/tmp|/var/run)"
SSH = re.compile(r"(^|[\s;&|(`$'\"])(sudo\s+(-\S+\s+)*)?(ssh|mosh|autossh)\s", re.I)
CLIENT = re.compile(r"(^|[\s;&|(`'\"/])" + CLIENTS + r"(\s|$|['\";|&)])", re.I)
REMOTE_FLAG = re.compile(r"(^|[\s;&|(])" + CLIENTS + r"\b[^;&|\n]*?(\s-h\s*|\s--host[=\s]+)(?!" + LOCAL + r")\S", re.I)
REMOTE_URL = re.compile(r"(postgres(ql)?|clickhouse|mysql|mongodb(\+srv)?|redis)://[^\s'\"]*@(?!" + LOCAL + r")[A-Za-z0-9.-]+", re.I)
REMOTE_DOCKER = re.compile(r"(DOCKER_HOST=|docker\s+(-H|--host|--context|context\s+use))", re.I)
REMOTE_KEYWORD = re.compile(r"\bhost\s*=\s*(?!" + LOCAL + r")[A-Za-z0-9][A-Za-z0-9.-]*", re.I)
REMOTE_ENV = re.compile(r"\b(PGHOST|CLICKHOUSE_HOST|MYSQL_HOST)=(?!" + LOCAL + r")\S", re.I)

B = r"(^|[\s;&|(`$'\"/])"
OBJECTS = r"(vault|vaults|item|items|account|accounts|document|documents|user|users|group|groups)"
OP_LIST = re.compile(B + r"op(\s+--?[A-Za-z][\w-]*(?:[= ](?!-)(?!" + OBJECTS + r"\b)\S+)?)*\s+" + OBJECTS
                     + r"\s+(list|ls)\b", re.I)
BW_LIST = re.compile(B + r"bw\s+list\b", re.I)
AGENT_LIST = re.compile(B + r"ssh-add\b[^;&|\n]*\s-[A-Za-z]*[lL]\b")
KEYCHAIN = re.compile(B + r"security\s+(find-generic-password|find-internet-password|find-key|dump-keychain|export)\b", re.I)

DB_MSG = ("Blocked by .claude/hooks/guard-prod-access.py: %s. Production databases are read only through the "
          "read-only wrapper on the server (docs/DIAG_USER_SETUP.md, sections 6a-6b), which keeps the time and resource "
          "limits. If the wrapper cannot answer the question, write the query down and ask the user. If this command "
          "only writes text that mentions these words, write the file with the editor tool instead.\n")
CRED_MSG = ("Blocked by .claude/hooks/guard-prod-access.py: %s. Do not search for credentials. Use only the access "
            "set up for this task; for anything else ask the user once, naming what you need and what will run with "
            "it, and wait. If this command only writes text that mentions these words, write the file with the "
            "editor tool instead.\n")


def verdict(cmd):
    if OP_LIST.search(cmd) or BW_LIST.search(cmd):
        return CRED_MSG % "a listing of password-manager vaults, items or accounts"
    if AGENT_LIST.search(cmd):
        return CRED_MSG % "a listing of the SSH agent's keys"
    if KEYCHAIN.search(cmd):
        return CRED_MSG % "a read of the macOS keychain"
    if SSH.search(cmd) and CLIENT.search(cmd):
        return DB_MSG % "a database client over ssh"
    if REMOTE_FLAG.search(cmd) or REMOTE_URL.search(cmd):
        return DB_MSG % "a database client pointed at a remote host"
    if CLIENT.search(cmd) and (REMOTE_DOCKER.search(cmd) or REMOTE_KEYWORD.search(cmd) or REMOTE_ENV.search(cmd)):
        return DB_MSG % "a database client reached through a remote docker host or a host setting"
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    message = verdict((data.get("tool_input") or {}).get("command") or "")
    if not message:
        return 0
    sys.stderr.write(message)
    return 2


if __name__ == "__main__":
    sys.exit(main())
