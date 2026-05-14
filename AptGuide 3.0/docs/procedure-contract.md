# Procedure Contract

Procedures are business workflows behind typed boundaries.

## Required Procedures

- `clarify`
- `room_search`
- `kb_qa`
- `appointment`
- `lease`
- `memory`
- `handoff`

## Procedure Input

Each procedure receives:

- conversation frame;
- validated understanding result;
- authenticated user context;
- tool/retrieval adapters through dependency injection.
- repository contracts for Agent state writes.

## Procedure Output

Each procedure returns:

- user-facing message;
- cards;
- actions;
- pending action;
- metadata;
- trace events.

## Write Operations

Appointment create/cancel and memory writes require confirmation. The LLM may identify the intent, but deterministic procedure code owns confirmation and execution.

## State Ownership

Procedures must not create private ad hoc state stores. Durable state goes through repository contracts:

- sessions and messages;
- pending actions;
- memories and memory candidates;
- handoff tickets and operator messages;
- trace events;
- procedure runs;
- audit events.

Business facts remain outside AptGuide 3.0:

- room availability;
- appointment state;
- lease state;
- user-sensitive profile fields.

Those facts must be read or written through lease internal tools.
