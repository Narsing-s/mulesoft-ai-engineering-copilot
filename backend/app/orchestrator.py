from dataclasses import dataclass
from typing import Callable

@dataclass
class AgentResult:
    agent: str
    answer: str
    confidence: float
    actions: list[str]

class Orchestrator:
    def __init__(self):
        self.agents: dict[str, Callable[[str], AgentResult]] = {
            "dataweave": self._dataweave,
            "mule-debugger": self._debugger,
            "munit": self._munit,
            "raml": self._raml,
            "flow-builder": self._flow,
            "general-mulesoft": self._general,
        }

    def route(self, message: str) -> AgentResult:
        text = message.lower()
        if any(x in text for x in ("dataweave", "%dw", "transform", "mapping")):
            agent = "dataweave"
        elif any(x in text for x in ("munit", "unit test", "test case")):
            agent = "munit"
        elif any(x in text for x in ("raml", "api spec", "openapi", "api contract")):
            agent = "raml"
        elif any(x in text for x in ("error", "exception", "failed", "stack trace", "why is")):
            agent = "mule-debugger"
        elif any(x in text for x in ("flow", "mule xml", "connector", "subflow")):
            agent = "flow-builder"
        else:
            agent = "general-mulesoft"
        return self.agents[agent](message)

    def _dataweave(self, _: str) -> AgentResult:
        return AgentResult("dataweave", "DataWeave request analyzed. Generate DW 2.0, execute it against supplied input, inspect the result, and repair failures.", 0.92, ["analyze_contract", "generate_dw", "execute", "validate", "self_repair"])

    def _debugger(self, _: str) -> AgentResult:
        return AgentResult("mule-debugger", "Mule failure analyzed. Classify the error, identify the likely root cause, propose a minimal fix, and validate it.", 0.90, ["classify_error", "analyze_context", "find_root_cause", "propose_fix", "validate_fix"])

    def _munit(self, _: str) -> AgentResult:
        return AgentResult("munit", "MUnit request analyzed. Cover happy paths, negative paths, mocks, assertions, and error handling.", 0.88, ["inspect_flow", "derive_cases", "generate_munit", "validate_tests"])

    def _raml(self, _: str) -> AgentResult:
        return AgentResult("raml", "API design request analyzed. Build resources, methods, types, examples, traits, and validation rules.", 0.88, ["extract_contract", "generate_raml", "validate_spec"])

    def _flow(self, _: str) -> AgentResult:
        return AgentResult("flow-builder", "Mule flow request analyzed. Design processors, variables, connectors, error handling, and Mule XML.", 0.87, ["extract_requirements", "design_flow", "generate_xml", "validate_xml"])

    def _general(self, _: str) -> AgentResult:
        return AgentResult("general-mulesoft", "MuleSoft engineering request received. The orchestrator can delegate to specialized MuleSoft agents.", 0.70, ["classify_request", "delegate"])
