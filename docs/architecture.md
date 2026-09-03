# Architecture

## Separation of responsibilities

The workflow separates three layers:

1. **Research contract** — stage definitions, required evidence, and output templates.
2. **Orchestration** — dependency checks, manifests, and human approval.
3. **Agent execution** — optional LLM workers that fill specific stage artifacts.

This separation prevents an LLM provider from becoming the source of truth for research state. The filesystem artifacts and manifest remain inspectable even when agent implementations change.

## Why file-based handoffs?

File-based handoffs make it possible to:

- compare revisions;
- assign stages to different agents;
- resume a partially completed project;
- audit which claims entered at which stage;
- require human approval without relying on ephemeral chat history.

## Research validity boundary

Workflow completion is not scientific validation. A completed literature template may still contain incomplete coverage, a proposal may still have weak identification, and a generated paper draft is not an empirical result. The architecture therefore treats review decisions and uncertainty statements as first-class state.

