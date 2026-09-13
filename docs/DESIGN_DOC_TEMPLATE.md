# Title

> **How to use this document as a template.** Goals and Non-Goals below describe only the change in this revision. So if the feature you design is not greenfield but an extension or additional feature, don't document the whole system you are building on top of. Instead, keep it as short as possible, as long as necessary: state only the part of the existing architecture needed to ground the new contract, and link to [README.md](../README.md) / the code for everything else — don't re-paste tables that aren't changing, they'll just go stale. Every subsection under **Proposal** is optional — delete any that this revision doesn't touch, rather than filling it with "unchanged." When you plan the *next* feature on top of this service, copy this file, fold the *previous* revision's Goals into Background as settled fact, and write fresh Goals/Non-Goals for only what you're adding.

## TL;DR

> 2-3 sentences: the problem, the proposed change, the expected outcome. A reviewer should be able to read this and the Goals below and decide whether the rest is relevant to them.

## Background

> Explain the context and why this document exists.

**See [README.md](../README.md) for current state of the service**

## Goals

> List the objectives this design aims to achieve.

## Non‑Goals

> What is explicitly out of scope.

## Proposal

> High-level description of the solution.

### Tech Stack *(delete if this revision adds no new layer/dependency)*

> Full stack is in [README.md](../README.md). List only rows this revision adds or changes.

| Layer   | Choice |
|---------|--------|
| NEW! ...| ...    |

### User Experience

> How end users will interact with the feature.

### Architecture

> What the system looks like, how it is structured, and how the components interact. Include diagrams if helpful.

**Sequence diagram:**

```mermaid
sequenceDiagram

```

### Evaluation Metrics *(delete if this revision doesn't change what/how success is measured)*

> How the change will be evaluated, including metrics, thresholds, and evaluation datasets.

### Data Model *(delete if unchanged)*

> Data structures, schemas, and storage changes. Include diagrams if helpful.

### APIs *(delete if unchanged)*

> Contract changes to the REST API, including request/response shapes, status codes, and error handling.

### Guardrails *(delete if unchanged)*

> Input/output rails, HTTP, deployment-level, node-level rails.

### Observability & Monitoring *(delete if unchanged)*

> What new signal this revision needs, and where it's surfaced (Langfuse / App Insights). Not a re-description of existing tracing.

### Inference Requirements *(delete if unchanged)*

> Only call out hardware/latency/throughput/cost implications if this revision changes them.

### Phased Scope *(delete if this revision doesn't shift the roadmap)*

#### Phase 1

#### Phase 2

### Testing

> How the change will be validated.

## Alternatives Considered

> Brief notes on other approaches and why they were rejected.

## Risks

> Potential pitfalls and mitigation strategies.

## Dependencies

> External systems or teams that must be involved.

## Open Questions

> Unresolved issues that need discussion.

## Appendix

- `README.md` - ...
- `PRD.md` - ...

## Revision History

| Date       | Comment     | Author       |
|------------|-------------|--------------|
| 2026-07-17 | First draft | my-username@ |
