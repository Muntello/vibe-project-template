# Architecture — {{PROJECT_NAME}}

> The living **specification** of this system: what it does and what it is made of.
> Kept current with the code. This is NOT a backlog of planned work or task specs —
> per-iteration plans live in the gitignored `.context/`, and the rationale behind decisions
> lives in `decisions/`.

## Overview

<!-- One paragraph: what this system is for and the problem it solves. -->

## Components

<!-- Each component has ONE responsibility. For each: what it does, how it is used, what it
     depends on. A reader should understand a component without reading its internals. -->

| Component | Responsibility | Depends on |
|-----------|----------------|------------|
| {{COMPONENT}} | <!-- single responsibility --> | <!-- deps --> |

## Data flow

<!-- How a request / event moves through the components, end to end. -->

## External dependencies & integrations

<!-- Databases, brokers, third-party APIs. Match production auth/port/rate-limit patterns
     (see ../AGENTS.md "External Service Dependencies"). -->

| Dependency | Purpose | Notes |
|------------|---------|-------|
| {{DB_NAME}} | Primary application database | <!-- ... --> |

## Why it is built this way

Significant decisions are recorded as ADRs in [`decisions/`](decisions/) — see that directory for
the "why" behind module boundaries, datastore choices, auth, and deployment.
