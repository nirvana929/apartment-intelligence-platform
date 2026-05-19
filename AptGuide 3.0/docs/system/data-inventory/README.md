# Data Inventory -- AptGuide 3.0

This folder documents every data source that AptGuide 3.0 reads from or writes to. It exists so that anyone working on the system can quickly answer:

- Where does a piece of data live?
- Who owns it?
- What are the retention / sensitivity rules?

## Files

| File | Covers |
|---|---|
| [sources.md](sources.md) | High-level source map and responsibilities |
| [mysql-schema.md](mysql-schema.md) | 11 MySQL tables, columns, purposes, sensitivity flags |
| [redis-keys.md](redis-keys.md) | Key prefix patterns, TTL settings, allowed inventory operations |
| [vector-collections.md](vector-collections.md) | Milvus collections, fields, chunking strategy |
| [lease-api.md](lease-api.md) | Lease API endpoints grouped by purpose |
| [external-ai.md](external-ai.md) | LLM, embedding, and observability service details |
| [inventory-runbook.md](inventory-runbook.md) | Safe inventory generation steps and prohibited dumps |

## Conventions

- All field names come from source code; no actual data values are included.
- Sensitive columns (message content, payloads, JSON blobs) are marked with `[SENSITIVE]`.
- API keys, passwords, tokens, and PII are never stored in these documents.
