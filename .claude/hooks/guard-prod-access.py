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
# The command is checked twice: as written, and with shell quoting removed (so `'ps''ql'` or
# `-h localhost'.example.com'` are seen the way the shell runs them). Host values are parsed and compared whole.
# This is a guard against mistakes, not a security boundary: a command hidden in a script the agent wrote is not
# seen. Exit 2 blocks the command and returns the message to the model; input it cannot parse is let through.
import json
import re
import shlex
import sys

CLIENTS = (r"(psql|pg_dump|pg_dumpall|pg_restore|clickhouse-client|clickhouse\s+client|mysql|mysqldump|mariadb"
           r"|mongo|mongosh|redis-cli|cqlsh|sqlite3)")
SSH = re.compile(r"(^|[\s;&|(`$'\"/])(sudo\s+(-\S+\s+)*)?(ssh|mosh|autossh)\s", re.I)
CLIENT = re.compile(r"(^|[\s;&|(`'\"/])" + CLIENTS + r"(\s|$|['\";|&)])", re.I)

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _host_of(part):
    part = part.strip()
    if part.startswith("/"):
        return "localhost"  # a unix socket directory
    if part.startswith("["):
        return part[1:part.find("]")].lower() if "]" in part else part.lower()
    if part.count(":") == 1:
        part = part.split(":", 1)[0]
    return part.lower()


def any_remote(value, empty_is_local=False):
    """True when any host of a value (libpq allows a comma list) is not local; an empty host counts as remote
    unless the caller knows it means the default local socket."""
    if value == "" and empty_is_local:
        return False
    return any(_host_of(p) not in LOCAL_HOSTS for p in value.split(","))


# each client invocation up to the next ; & | or newline, then EVERY host flag in it (the client uses the last one)
CLIENT_SEGMENT = re.compile(r"(^|[\s;&|(/])" + CLIENTS + r"\b(?P<s>[^\n]*)", re.I)  # to the end of the line
FLAG_HOST = re.compile(r"\s(-[A-Za-z]*h|--ho(?:st?)?=?)\s*['\"]?(?P<h>[^\s'\";&|()]*)")  # -h, bundled -Xh, --ho/--hos/--host
URL_AUTH = re.compile(r"(postgres(ql)?|clickhouse|mysql|mongodb(\+srv)?|redis)://(?P<a>[^\s/'\"]*)", re.I)
KEYWORD_HOST = re.compile(r"\bhost(addr)?\s*=\s*['\"]?(?P<h>[^\s'\";&|()]*)", re.I)
ENV_HOST = re.compile(r"\b(PGHOST|PGHOSTADDR|CLICKHOUSE_HOST|MYSQL_HOST)=['\"]?(?P<h>[^\s'\";&|()]*)", re.I)
REMOTE_DOCKER = re.compile(r"(DOCKER_HOST=|docker\s+(-H|--host|--context|context\s+use))", re.I)


def _url_remote(authority):
    # libpq ends the authority at "/" only, other clients also at "?" or "#": check the host both ways
    libpq = re.split(r"[?#]", authority.rsplit("@", 1)[-1], maxsplit=1)[0]
    short = re.split(r"[?#]", authority, maxsplit=1)[0]
    other = short.rsplit("@", 1)[-1]
    return any_remote(libpq, empty_is_local=(authority == "")) or any_remote(other, empty_is_local=(short == ""))


def remote_flag_or_url(cmd):
    for seg in CLIENT_SEGMENT.finditer(cmd):
        if any(any_remote(m.group("h")) for m in FLAG_HOST.finditer(seg.group("s"))):
            return True
    return any(_url_remote(m.group("a")) for m in URL_AUTH.finditer(cmd))


def remote_keyword_or_env(cmd):
    return any(any_remote(m.group("h")) for m in KEYWORD_HOST.finditer(cmd)) or \
        any(any_remote(m.group("h")) for m in ENV_HOST.finditer(cmd))


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


def unquoted(cmd):
    """The command with shell quoting removed and quoted pieces joined, words separated by single spaces.
    None when the quoting cannot be parsed."""
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()")
        lex.whitespace_split = True
        lex.commenters = ""  # bash comments only start a word; keep every word, accept false positives
        return " ".join(lex)
    except ValueError:
        return None


def check(cmd):
    if OP_LIST.search(cmd) or BW_LIST.search(cmd):
        return CRED_MSG % "a listing of password-manager vaults, items or accounts"
    if AGENT_LIST.search(cmd):
        return CRED_MSG % "a listing of the SSH agent's keys"
    if KEYCHAIN.search(cmd):
        return CRED_MSG % "a read of the macOS keychain"
    if SSH.search(cmd) and CLIENT.search(cmd):
        return DB_MSG % "a database client over ssh"
    if remote_flag_or_url(cmd):
        return DB_MSG % "a database client pointed at a remote host"
    if CLIENT.search(cmd) and (REMOTE_DOCKER.search(cmd) or remote_keyword_or_env(cmd)):
        return DB_MSG % "a database client reached through a remote docker host or a host setting"
    return None


def verdict(cmd):
    flat = unquoted(cmd)
    if flat is None:
        # fail closed: quoting the guard cannot read, around a database client or a connection URL
        if CLIENT.search(cmd) or URL_AUTH.search(cmd) or CLIENT.search(re.sub(r"['\"\\]", "", cmd)):
            return DB_MSG % "a database command whose quoting the guard cannot parse"
        flat = re.sub(r"['\"\\]", "", cmd)
    return check(cmd) or check(flat)


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
