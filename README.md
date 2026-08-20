# MuleSoft AI Engineering Copilot

An AI-native engineering platform for MuleSoft developers, integration engineers, architects, and production-support teams.

## Vision

Go beyond code generation: **Understand → Generate → Validate → Debug → Fix → Explain**.

This is a new product and is intentionally independent from `dw-ai-copilot`.

## Current runnable foundation

- FastAPI backend with specialized-agent routing
- Groq/OpenAI-compatible model provider abstraction
- Offline/mock mode when no API key is configured
- Agent-specific prompts for DataWeave, debugging, RAML, Mule flows, and MUnit
- Generation + deterministic response validation pipeline
- Verification metadata returned by the API
- CORS-enabled API
- Functional browser UI in `frontend/index.html`
- Docker Compose configuration

## Run locally

```bash
cp .env.example .env
# For offline mode leave AI_PROVIDER=mock
# For Groq set AI_PROVIDER=groq and AI_API_KEY=<your-key>
docker compose up --build
```

Backend health: `http://localhost:8000/health`

Open `frontend/index.html` in a browser and use the Copilot UI. The UI calls `http://localhost:8000` by default; set `localStorage.COPILOT_API` if the backend is hosted elsewhere.

## AI configuration

The backend uses an OpenAI-compatible chat-completions interface. The default remote configuration is Groq. Provider configuration is environment-based, so keys are never committed to the repository.

```text
AI_PROVIDER=groq
AI_API_KEY=<secret>
AI_BASE_URL=https://api.groq.com/openai/v1
AI_MODEL=llama-3.3-70b-versatile
```

For offline development:

```text
AI_PROVIDER=mock
AI_API_KEY=
```

## Product architecture

```text
Web UI
  ↓
FastAPI
  ↓
AI Orchestrator
  ├── DataWeave Agent
  ├── Mule Debugger Agent
  ├── Flow Builder Agent
  ├── RAML Agent
  └── MUnit Agent
  ↓
Generation Pipeline
  ↓
Validation / Execution Adapters
  ↓
Verified response
```

The next execution milestone is a deterministic DataWeave runtime adapter. The API already exposes the `DW_EXECUTOR_URL` configuration point for that service; until an executor is connected, the system does **not** claim that generated DataWeave was actually executed.

## Long-term capabilities

- Mule project indexing and repository-aware Q&A
- RAG grounded in MuleSoft documentation and project knowledge
- SQL and connector expertise
- Architecture agent
- MUnit execution
- Self-repair loops based on real execution errors
- Multi-model routing
- Enterprise authentication and auditability
