from fastapi import FastAPI
from pydantic import BaseModel, Field

from .orchestrator import Orchestrator

app = FastAPI(title="MuleSoft AI Engineering Copilot", version="0.1.0")
orchestrator = Orchestrator()

class ChatRequest(BaseModel):
    message: str
    context: dict = Field(default_factory=dict)

@app.get("/health")
def health():
    return {"status": "ok", "service": "mulesoft-ai-engineering-copilot", "version": "0.1.0"}

@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    result = orchestrator.route(request.message)
    return {
        "status": "ok",
        "agent": result.agent,
        "answer": result.answer,
        "confidence": result.confidence,
        "actions": result.actions,
    }
