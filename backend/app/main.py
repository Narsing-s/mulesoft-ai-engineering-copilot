from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="MuleSoft AI Engineering Copilot", version="0.1.0")

class ChatRequest(BaseModel):
    message: str
    context: dict = Field(default_factory=dict)

@app.get("/health")
def health():
    return {"status": "ok", "service": "mulesoft-ai-engineering-copilot"}

@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    return {"status": "accepted", "message": request.message, "next": "orchestrator"}
