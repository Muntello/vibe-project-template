# Architecture Decision Records (ADRs)

This directory holds short records of **why** significant decisions were made — context that
would otherwise clutter the main documentation. The main docs describe what the system *is*
(`../ARCHITECTURE.md`); ADRs explain *why it is that way*.

## When to write an ADR

Write one when a decision is hard to reverse, affects module boundaries, or future-you will ask
"why on earth did we do it this way": choice of datastore, auth method, a module-boundary split,
a deployment approach, dropping an obvious-seeming option.

Do NOT write one for routine, easily-reversed choices.

## Format

- One file per decision: `NNNN-<slug>.md` (zero-padded, monotonically increasing).
- Copy `0000-adr-template.md` to the next number.
- Keep it short. Three sections: **Context -> Decision -> Consequences.**
- ADRs are immutable once Accepted. To change a decision, write a new ADR and mark the old one
  `Superseded by NNNN`.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-two-user-access-model.md) | Two-user production access model | Accepted |
