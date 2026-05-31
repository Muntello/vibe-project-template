# 0001. Two-user production access model

- **Status:** Accepted
- **Date:** 2026-05-31

## Context

AI agents need access to production servers to investigate issues, but unrestricted access is
dangerous: an agent could modify config, restart services, or write to databases without intent.
We want investigation to be safe by default while still allowing deliberate, approved changes.
Production servers also run fail2ban, so credential mistakes carry a banning cost.

## Decision

We will provision two isolated server users with separate SSH keys:

- **`diag`** (Diagnostic mode): read-only. Reads logs, runs `SELECT` queries, checks service
  status. Cannot modify anything. This is the default for "just looking".
- **`{{DEPLOY_USER}}`** (Investigation mode): full access. Every write operation requires explicit
  human approval before the agent acts.

Agents start in Diagnostic mode and escalate to Investigation only when a change is approved.

## Consequences

- Investigation is safe by default — the common case (reading) cannot cause damage.
- Two key pairs and two user setups must be provisioned and kept in sync (see
  `../DIAG_USER_SETUP.md` and `../AGENT_SERVER_ACCESS.md`).
- The model is advisory at the process layer: the `diag` user enforces read-only at the OS level,
  but Investigation-mode discipline ("ask before writing") depends on the agent following
  `../../AGENTS.md`.
