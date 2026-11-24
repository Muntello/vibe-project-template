# Hooks

A rule in `AGENTS.md` tells the agent what not to do; a hook stops it. Rules that protect production or
credentials are worth backing with a hook, because an agent that is sure of itself will sooner or later reason its
way past a written rule.

## `guard-prod-access.py`

A Claude Code `PreToolUse` hook for the Bash tool. It refuses:

- a database client run over ssh, or pointed at a remote host by a flag, a URL, a host setting or a remote Docker
  daemon. Production is read through the wrapper on the server (`docs/DIAG_USER_SETUP.md`, sections 6a-6b), so
  `ssh diag@host diag-sql < query.sql` still works;
- listings of password-manager vaults, items and accounts (`op`, `bw`), of the SSH agent's keys (`ssh-add -l/-L`),
  and reads of the macOS keychain. Reading one named secret (`op read op://...`) is not affected.

On a match it exits 2 and the agent gets a message that says what to do instead.

It reads only the command line. A command hidden inside a script the agent wrote first is not seen, so treat it as
a guard against mistakes, not as a security boundary. The boundary is the database role and its limits.

## Install

Per project, in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 -I \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard-prod-access.py" }
        ]
      }
    ]
  }
}
```

The agent can edit a file inside its own project. For a guard it cannot switch off, copy the script to a
location it cannot write (for example `sudo install -o root -m 0755 guard-prod-access.py /usr/local/lib/agent-hooks/`)
and register that path in your user settings (`~/.claude/settings.json`), so it applies to every project.

The hook is for Claude Code. Other agents need their own mechanism, such as their sandbox and approval settings.

## Test it

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ssh diag@host psql -c \"select 1\""}}' \
  | python3 -I .claude/hooks/guard-prod-access.py; echo "exit $?"
# exit 2 and the message
```
