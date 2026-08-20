from dataclasses import dataclass

@dataclass
class AgentResult:
    agent: str
    answer: str
    confidence: float = 0.0

class Orchestrator:
    def route(self, message: str) -> AgentResult:
        text = message.lower()
        if "dataweave" in text or "%dw" in text:
            agent = "dataweave"
        elif "munit" in text:
            agent = "munit"
        elif "raml" in text or "api spec" in text:
            agent = "raml"
        elif "error" in text or "exception" in text or "failed" in text:
            agent = "mule-debugger"
        elif "flow" in text or "mule xml" in text:
            agent = "flow-builder"
        else:
            agent = "general-mulesoft"
        return AgentResult(agent=agent, answer=f"Routed to {agent} agent. Agent implementation is next.")
