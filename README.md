# MuleSoft AI Engineering Copilot

An AI-native engineering platform for MuleSoft developers, integration engineers, architects, and production-support teams.

## Vision

Go beyond code generation: **Understand → Generate → Execute → Validate → Debug → Fix → Explain**.

The platform is designed as a new product and is intentionally independent from `dw-ai-copilot`.

## Core capabilities

- DataWeave generation, explanation, optimization, and debugging
- Mule XML flow generation and repair
- RAML / API specification generation
- MUnit test generation
- Mule runtime and connector error diagnosis
- Mule project analysis and repository-aware Q&A
- SQL assistance for integration projects
- Architecture and integration design assistance
- RAG grounded in MuleSoft documentation and project knowledge
- Model routing and agent orchestration
- Deterministic execution and validation where possible

## Product principle

An LLM response is not considered complete just because code was generated. Code should be validated and, where an execution engine is available, executed against representative input before being presented as verified.

## Initial architecture

```text
Web UI
  ↓
API / Application Layer
  ↓
AI Orchestrator
  ├── DataWeave Agent
  ├── Mule Debugger Agent
  ├── Flow Builder Agent
  ├── RAML Agent
  ├── MUnit Agent
  ├── SQL Agent
  └── Architecture Agent
  ↓
Knowledge / RAG ← MuleSoft docs + project index
  ↓
Execution & Validation
  ↓
Verified response
```

## Repository structure

```text
frontend/          Web application
backend/           API and application services
agents/            Specialized MuleSoft agents
orchestrator/      Agent routing and workflow coordination
rag/               Retrieval and knowledge services
project-analyzer/  Mule project indexing and code intelligence
execution/         Deterministic execution/validation adapters
knowledge/         Curated knowledge and ingestion tooling
tests/             Cross-component tests
docs/              Product and architecture documentation
deployment/        Deployment configuration
```

## Status

Early foundation. The repository is being built as a separate product from the existing DataWeave Copilot.
