# Two coding agents on one VPS

A Linux VPS can run Codex and Claude Code while you work from a phone or desktop. This example gives each agent a development clone, an independent GitHub identity and a service that starts at boot. The administrator manages the host. For access to a live application, follow the project's [production access guide](../../docs/AGENT_SERVER_ACCESS.md).

## Which account does what?

| Connection | Codex example | Claude Code example |
| --- | --- | --- |
| SSH from the operator's computer | Dedicated key for Linux user `codex-agent` | Different key for `claude-agent` |
| Mobile app to agent | ChatGPT account paired with Codex on the VPS | Claude account signed in on the VPS and iPhone |
| GitHub push and PR | GitHub user `example-codex` | GitHub user `example-claude` |
| Git commit author | Name and verified email for `example-codex` | Name and verified email for `example-claude` |
| Git commit signature | Signing key owned by `codex-agent` on the VPS | Separate signing key owned by `claude-agent` on the VPS |

Create both Linux users without sudo, with private home directories. Put each user's public login key in its own `~/.ssh/authorized_keys`. Keep the corresponding private login keys on the operator's device or in its SSH agent. Test both SSH aliases with agent forwarding disabled. Check that each alias logs in as the intended user and that SSH password authentication is disabled. Keep the administrator's key separate.

## Prepare each working copy

Run these commands once as each Linux user. Choose that agent's GitHub account in the device authorization screen. Grant the account **Write** on the repositories where it will push branches and open PRs.

```sh
gh auth login --hostname github.com --git-protocol https --web
gh api user --jq .login
gh auth setup-git --hostname github.com
git config --global user.name 'AGENT_GITHUB_LOGIN'
git config --global user.email 'AGENT_VERIFIED_EMAIL'
mkdir -p ~/workspace
git clone https://github.com/EXAMPLE_ORG/EXAMPLE_REPO.git ~/workspace/sample-app
cd ~/workspace/sample-app
git var GIT_AUTHOR_IDENT
```

Replace the uppercase example values. On a headless server, `gh` can fall back to a token file. Check that its owner is the intended user and its mode is `0600`. Give each user its own clone even when both work on the same repository. Open the clone itself as the project so its root instructions and test commands are in scope.

## Sign commits as each agent

Run the setup once as `codex-agent` and again as `claude-agent`, using Git 2.34 or later and OpenSSH. Each Linux user generates its own Ed25519 key in its own home directory. If the path already holds another key or an incomplete pair, choose an unused filename. The empty passphrase lets the service sign after a reboot without an interactive unlock. Keep the private file on the VPS, readable only by its owner (mode `0600`).

```sh
signing_key="$HOME/.ssh/git-signing-ed25519"
install -d -m 700 "$HOME/.ssh"
if [ ! -e "$signing_key" ] && [ ! -e "$signing_key.pub" ]; then
  ssh-keygen -q -t ed25519 -N '' -C "$(id -un) git signing" -f "$signing_key"
fi
ssh-keygen -lf "$signing_key.pub"
cat "$signing_key.pub"
```

In the matching GitHub account, open **Settings → SSH and GPG keys → New SSH key**. Set **Key type** to **Signing Key**, paste the public `.pub` line and save. Check the fingerprint under **Signing keys** against the one printed above. Register this key only for signing. The account's **Authentication keys** grant Git access over SSH. [GitHub key settings](https://github.com/settings/keys)

Enable automatic signing for that Linux user in the same shell. In the agent's clone, confirm that the effective committer email is verified in the matching GitHub account.

```sh
git config --global gpg.format ssh
git config --global user.signingKey "$signing_key"
git config --global commit.gpgSign true
git var GIT_COMMITTER_IDENT
```

### Check Verified on GitHub

For each agent, make an ordinary `git commit` on a topic branch and push it. Open that exact commit on GitHub and click **Verified** to inspect the signature. To check from the VPS, set `repo` to the repository that received the push (the fork for a fork-based PR).

```sh
repo='EXAMPLE_OWNER/EXAMPLE_REPO'
sha=$(git rev-parse HEAD)
gh api "repos/$repo/commits/$sha" \
  --jq '{committer: .committer.login, email: .commit.committer.email, verified: .commit.verification.verified, reason: .commit.verification.reason}'
```

Expect the agent's GitHub login and email, `verified: true` and `reason: "valid"`. If GitHub reports `unknown_key`, check the fingerprint and key type in that account. For `unsigned`, check `git config --show-origin --get commit.gpgSign` in the clone and confirm the commit was created after enabling signing. [GitHub verification results](https://docs.github.com/en/rest/commits/commits#get-a-commit)

## Install the user instructions

Review [the shared defaults](../../agent-defaults/AGENTS.md) at the revision you intend to install. Copy that file to each user's own instruction path (the default paths are shown below). If a file already exists, review and merge its contents before installing. A copy keeps later project edits from silently changing the rules for every project on the host.

| Agent | Destination in that user's home |
| --- | --- |
| Codex | `~/.codex/AGENTS.md` (under `$CODEX_HOME` if set) |
| Claude Code | `~/.claude/CLAUDE.md` (under `$CLAUDE_CONFIG_DIR` if set) |

Compare the installed files with the reviewed source using `sha256sum` after a direct copy. Start a new chat in the clone to pick up the instructions. A non-empty Codex `AGENTS.override.md` in the Codex home directory takes precedence over the file in the table. [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md) · [Claude Code memory](https://code.claude.com/docs/en/memory)

## Connect the phone

- **Codex.** Install and sign in to the CLI as `codex-agent`. In a CLI version with experimental manual pairing, run `codex remote-control start` and then `codex remote-control pair`. Enter the temporary code in the mobile app if manual pairing is available. Desktop access is a separate connection. To open the project over SSH on a desktop, select the alias for `codex-agent` and its clone. [CLI reference](https://learn.chatgpt.com/docs/cli/reference#codex-remote-control) · [Remote connections](https://learn.chatgpt.com/docs/remote-connections)
- **Claude Code.** As `claude-agent`, run `claude auth login`, then start `claude remote-control --name "Sample app" --spawn same-dir --permission-mode default` in the clone. Complete the initial workspace trust and Remote Control prompts in a terminal. Open **Code** in the Claude app under the same account and select **Sample app**. Stop the manual server gracefully before starting its system service. [Claude Code Remote Control](https://code.claude.com/docs/en/remote-control)

## Start both services at boot

Use two system-level systemd units with separate `User=` values. Each unit needs its user's `HOME`, a `PATH` containing the installed CLI and its dependencies, and its own clone as `WorkingDirectory=`. Order both after `network-online.target`, enable them under `multi-user.target`, and allow time between restart attempts.

| Unit | Start and stop behavior |
| --- | --- |
| `codex-agent.service` | Start the managed daemon with `codex remote-control start`. Stop it with `codex remote-control stop`. The launcher exits after detaching. On systemd 250 or newer, `Type=exec` with `ExitType=cgroup` tracks the remaining processes. A brief connection conflict can follow a restart. Allow a delayed retry and verify that Remote Control actually connects. |
| `claude-agent.service` | Run the same `claude remote-control` command as a foreground process with `Type=exec`. Use `KillSignal=SIGINT` for a graceful stop and `Restart=always` with a delay to recover when the server exits. |

Use absolute executable paths in the units. Start each server only once. Stop any manually launched instance before handing it over to systemd. The GitHub tokens and the two CLI logins stay in their respective users' home directories.

## Verify from the phone

1. Disconnect SSH. Send `whoami` and `pwd` to each agent from its mobile app. Expect its own Linux username and the path to its clone.
2. In each clone, check `gh api user --jq .login`, `git var GIT_AUTHOR_IDENT` and `git push --dry-run origin HEAD:refs/heads/agent-access-check`. A dry run exercises Git push authentication without publishing a branch.
3. With approval for the interruption, reboot the VPS. Before logging in as either agent, repeat the mobile check. From the administrator account, verify both units are enabled and inspect this boot's logs for a successful remote connection.
4. If the VPS also provides a fixed outbound IP for an integration, repeat that integration's usual read-only request through its normal route before and after the reboot.
