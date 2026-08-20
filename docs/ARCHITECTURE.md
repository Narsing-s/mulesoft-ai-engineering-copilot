# Architecture

## Design goals

1. MuleSoft-specialized rather than general-purpose chat.
2. Deterministic validation wherever possible.
3. Project-aware context without leaking secrets.
4. Provider-neutral model routing.
5. Agent outputs represented as structured artifacts, not only prose.
6. Offline/local execution adapters where practical.

## Request lifecycle

```text
User request
   ↓
Intent + task classification
   ↓
Context assembly
   ├── conversation
   ├── project index
   ├── retrieved documentation
   └── execution history
   ↓
Agent selection / orchestration
   ↓
Plan
   ↓
Generate artifact
   ↓
Static validation
   ↓
Execution (when supported)
   ↓
Failure analysis + repair loop
   ↓
Final artifact + evidence + explanation
```

## Agent contract

Every agent should eventually implement a common contract:

- `can_handle(request)`
- `plan(context)`
- `generate(context, plan)`
- `validate(artifact, context)`
- `repair(failure, context)`
- `explain(result, context)`

## Security boundaries

Secrets, tokens, credentials, private keys, and production payloads must never be placed into prompts or indexed by default. Redaction belongs in the context pipeline, before model calls and vector indexing.

## MVP sequence

### Phase 1

- Application shell
- Orchestrator
- DataWeave agent
- Mule error debugger
- RAML agent
- Flow builder
- Provider abstraction
- Health/config endpoints

### Phase 2

- MUnit agent
- Project analyzer
- RAG ingestion/retrieval
- Execution adapters
- Validation/repair loop

### Phase 3

- Multi-agent planning
- Repository-wide dependency intelligence
- Architecture agent
- Enterprise controls and auditability
