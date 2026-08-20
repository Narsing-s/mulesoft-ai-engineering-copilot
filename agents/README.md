# Agents

Initial specialized agents:

- `dataweave` — transformations, explanations, optimization, repair
- `mule-debugger` — runtime/DW/connector error diagnosis
- `flow-builder` — Mule XML flow design and repair
- `raml` — API contract generation and review
- `munit` — test generation and test-case reasoning
- `sql` — integration-oriented SQL generation and review
- `architecture` — integration architecture and design decisions

Agents must produce structured artifacts and validation metadata. They should not silently claim that generated code was executed when it was not.
