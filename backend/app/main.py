from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .contracts import ChatRequest, ChatResponse
from .orchestrator import Orchestrator

app = FastAPI(title="MuleSoft AI Engineering Copilot", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
orchestrator = Orchestrator()

@app.get("/health")
def health():
    return {"status": "ok", "service": "mulesoft-ai-engineering-copilot", "version": "0.2.0"}

@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = orchestrator.route(request.message, request.context)
    return ChatResponse(status="ok", agent=result.agent, answer=result.answer, confidence=result.confidence, actions=result.actions, verified=result.verified, attempts=result.attempts, validation=result.validation)
