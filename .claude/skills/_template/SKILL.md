---
name: {{skill-name}}
description: {{One sentence on what this covers and when it applies — this is the only text the agent reads before deciding to load the body. End with the phrasings people actually type, in every language they use: «посмотри на проде», "why did the webhook fail", deploy, rollback.}}
---

# {{Skill Title}}

One or two sentences on what this covers and, more usefully, what happens to someone who does
not know it. Skip the preamble — the agent already decided to read this.

## {{The first thing that bites}}

State the mechanic, then the failure it causes:

> Deduplication is on `SHA256(raw body)`, not an event id — the provider sends none.
> Consequence: two genuinely distinct events with byte-identical bodies collapse into one.

Tables earn their place when there are parallel cases to compare:

| Thing | Where it lives | Gotcha |
|---|---|---|
| | | |

## {{A procedure, if this skill is one}}

Numbered steps, each with the reason it exists. A step whose reason is unstated will be skipped
the first time it seems inconvenient.

## Deliberate absences

Anything that looks like a gap but is a decision. Without this, someone eventually "fixes" it:

> Retention events are intentionally not dispatched — the platform has no native equivalent.
> Adding one would be a regression, not a gap.

## Flags and dark code

Anything that reads as live but runs behind a default-off flag. Name the flag, its default, and
what has to be true before flipping it. This is the most reliable way to send someone debugging
a bug that does not exist.

## Verifying

What actually counts as evidence for this area — a real request, a row in the log table, a
query against the running system. Not "the command exited zero".

---

Guidance for writing this file — [../README.md](../README.md).
No line numbers. No copied business data. No status markers.
