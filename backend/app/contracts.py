from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    context: dict = Field(default_factory=dict)

class ChatResponse(BaseModel):
    status: str
    agent: str
    answer: str
    confidence: float
    actions: list[str]
    verified: bool
    attempts: int
    validation: str
