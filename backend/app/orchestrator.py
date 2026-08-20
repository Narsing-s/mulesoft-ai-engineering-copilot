from dataclasses import dataclass

from .pipeline import EngineeringPipeline

@dataclass
class AgentResult:
    agent: str
    answer: str
    confidence: float
    actions: list[str]
    verified: bool = False
    attempts: int = 0
    validation: str = "not_run"

class Orchestrator:
    def __init__(self):
        self.pipeline = EngineeringPipeline()

    def route(self, message: str, context: dict | None = None) -> AgentResult:
        text = message.lower()
        if any(x in text for x in ("dataweave", "%dw", "transform", "mapping")):
            agent, confidence, actions = "dataweave", 0.92, ["analyze_contract", "generate_dw", "validate", "self_repair"]
        elif any(x in text for x in ("munit", "unit test", "test case")):
            agent, confidence, actions = "munit", 0.88, ["inspect_flow", "derive_cases", "generate_munit", "validate_tests"]
        elif any(x in text for x in ("raml", "api spec", "openapi", "api contract")):
            agent, confidence, actions = "raml", 0.88, ["extract_contract", "generate_raml", "validate_spec"]
        elif any(x in text for x in ("error", "exception", "failed", "stack trace", "why is")):
            agent, confidence, actions = "mule-debugger", 0.90, ["classify_error", "analyze_context", "find_root_cause", "propose_fix", "validate_fix"]
        elif any(x in text for x in ("flow", "mule xml", "connector", "subflow")):
            agent, confidence, actions = "flow-builder", 0.87, ["extract_requirements", "design_flow", "generate_xml", "validate_xml"]
        else:
            agent, confidence, actions = "general-mulesoft", 0.70, ["classify_request", "delegate"]

        result = self.pipeline.run(agent, message, context)
        return AgentResult(agent, result.answer, confidence, actions, result.verified, result.attempts, result.validation)
