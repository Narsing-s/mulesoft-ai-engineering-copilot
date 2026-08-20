import json
import re
from dataclasses import dataclass

from .llm import LLMClient, LLMError
from execution.dw_executor import DataWeaveExecutor


@dataclass
class PipelineResult:
    answer: str
    verified: bool
    attempts: int
    validation: str


class EngineeringPipeline:
    def __init__(self):
        self.llm = LLMClient()
        self.dw = DataWeaveExecutor()

    def run(self, agent: str, message: str, context: dict | None = None) -> PipelineResult:
        context = context or {}
        system = self._system_prompt(agent)
        user = self._user_prompt(message, context)
        last_answer = ""

        for attempt in range(1, 4):
            try:
                answer = self.llm.generate(system, user)
            except LLMError as exc:
                return PipelineResult(str(exc), False, attempt - 1, "provider_error")

            last_answer = answer
            validation = self._validate(agent, answer)

            if validation == "pass" and agent == "dataweave":
                execution = self._execute_dw(answer, context)
                if execution["executed"] and execution["status"] == "executed":
                    return PipelineResult(
                        answer + "\n\nExecution result:\n" + json.dumps(execution["output"], indent=2),
                        True,
                        attempt,
                        "executed_and_validated",
                    )
                if execution["status"] == "execution_error":
                    user = self._repair_prompt(message, context, answer, execution)
                    system += "\nFix the transformation based on the execution error. Return the complete corrected DataWeave."
                    continue
                return PipelineResult(answer, False, attempt, execution["status"])

            if validation == "pass":
                return PipelineResult(answer, True, attempt, "validated")

            user = self._repair_prompt(message, context, answer, {
                "status": validation,
                "executed": False,
                "error": validation,
            })

        return PipelineResult(last_answer, False, 3, "max_repair_attempts")

    def _execute_dw(self, answer: str, context: dict) -> dict:
        match = re.search(r"```(?:dataweave|dw)?\s*(%dw[\s\S]*?)```", answer, re.I)
        script = match.group(1).strip() if match else ""
        input_payload = context.get("input") or context.get("inputPayload")

        if not script or input_payload is None:
            return {
                "status": "not_configured",
                "executed": False,
                "output": None,
                "error": "Provide context.input/context.inputPayload and a fenced DataWeave script.",
            }

        if not isinstance(input_payload, str):
            input_payload = json.dumps(input_payload)

        return self.dw.execute(script, input_payload, context.get("inputMimeType", "application/json"))

    def _user_prompt(self, message: str, context: dict) -> str:
        return (
            f"Request:\n{message}\n\nContext:\n{json.dumps(context, default=str, indent=2)}\n\n"
            "Return implementation-ready MuleSoft output. Put generated code in fenced blocks. "
            "Never claim execution unless an execution result is explicitly available."
        )

    def _repair_prompt(self, message: str, context: dict, answer: str, execution: dict) -> str:
        return self._user_prompt(message, context) + (
            f"\n\nPrevious answer:\n{answer}\n\n"
            f"Validation/execution feedback:\n{json.dumps(execution, default=str)}\n\n"
            "Repair the answer and return the complete corrected artifact."
        )

    def _system_prompt(self, agent: str) -> str:
        prompts = {
            "dataweave": "You are a senior MuleSoft DataWeave 2.0 engineer. Produce idiomatic, executable DW. Consider nulls, arrays, objects, types, dates, and edge cases.",
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
