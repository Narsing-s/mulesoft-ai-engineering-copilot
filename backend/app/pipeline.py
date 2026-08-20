from dataclasses import dataclass
from .llm import LLMClient, LLMError

@dataclass
class PipelineResult:
    answer: str
    verified: bool
    attempts: int
    validation: str

class EngineeringPipeline:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, agent: str, message: str, context: dict | None = None) -> PipelineResult:
        context = context or {}
        system = self._system_prompt(agent)
        user = f"Request:\n{message}\n\nContext:\n{context}\n\nReturn a practical MuleSoft engineering answer. Put generated code in fenced blocks. Do not claim code was executed unless an execution result is explicitly available."
        try:
            answer = self.llm.generate(system, user)
        except LLMError as exc:
            return PipelineResult(str(exc), False, 0, "provider_error")
        validation = self._validate(agent, answer)
        return PipelineResult(answer, validation == "pass", 1, validation)

    def _system_prompt(self, agent: str) -> str:
        prompts = {
            "dataweave": "You are a senior MuleSoft DataWeave 2.0 engineer. Prefer correct, idiomatic DW and consider nulls, arrays, objects, types, dates, and edge cases.",
            "mule-debugger": "You are a senior MuleSoft production support engineer. Diagnose from evidence, separate facts from hypotheses, and give the smallest safe fix.",
            "raml": "You are a MuleSoft API architect. Produce valid RAML/OAS contracts with reusable types, examples, validation, and consistent naming.",
            "flow-builder": "You are a senior MuleSoft integration architect. Design maintainable Mule XML flows with variables, error handling, connectors, and sensible boundaries.",
            "munit": "You are a senior MUnit engineer. Generate meaningful tests for success, failure, mocks, assertions, and edge cases.",
            "general-mulesoft": "You are a senior MuleSoft engineer. Give implementation-ready guidance and identify assumptions clearly.",
        }
        return prompts.get(agent, prompts["general-mulesoft"])

    def _validate(self, agent: str, answer: str) -> str:
        if not answer.strip():
            return "fail:empty"
        if agent == "dataweave" and "%dw" not in answer.lower() and "offline mode" not in answer.lower():
            return "warn:no-dw-header"
        if agent == "raml" and "#%raml" not in answer.lower() and "offline mode" not in answer.lower():
            return "warn:no-raml-header"
        return "pass"
