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

                if execution.get("executed") and execution.get("status") == "executed":
                    output = execution.get("output")

                    # The executor may return HTTP 200 while the DW engine
                    # reports success=false. Only verified DW execution counts.
                    if isinstance(output, dict) and output.get("success") is False:
                        execution_error = output.get("error") or "DataWeave execution failed"
                        user = self._repair_prompt(
                            message,
                            context,
                            answer,
                            {
                                "status": "execution_error",
                                "executed": True,
                                "success": False,
                                "error": execution_error,
                                "output": output.get("output"),
                            },
                        )
                        system += (
                            "\nThe previous DataWeave failed during REAL execution. "
                            "Use the exact execution error to repair it. "
                            "Return the COMPLETE corrected DataWeave script."
                        )
                        continue

                    return PipelineResult(
                        answer + "\n\nExecution result:\n" + json.dumps(output, indent=2),
                        True,
                        attempt,
                        "executed_and_verified",
                    )

                if execution.get("status") == "execution_error":
                    user = self._repair_prompt(message, context, answer, execution)
                    system += (
                        "\nThe DataWeave execution service returned an error. "
                        "Repair the transformation using the exact feedback and "
                        "return the complete corrected DataWeave."
                    )
                    continue

                return PipelineResult(
                    answer,
                    False,
                    attempt,
                    execution.get("status", "execution_failed"),
                )

            if validation == "pass":
                return PipelineResult(answer, True, attempt, "validated")

            user = self._repair_prompt(
                message,
                context,
                answer,
                {
                    "status": validation,
                    "executed": False,
                    "error": validation,
                },
            )

        return PipelineResult(last_answer, False, 3, "max_repair_attempts")

    def _execute_dw(self, answer: str, context: dict) -> dict:
        match = re.search(r"```(?:dataweave|dw)?\s*(%dw[\s\S]*?)```", answer, re.I)
        script = match.group(1).strip() if match else ""
        input_payload = context.get("input")
        if input_payload is None:
            input_payload = context.get("inputPayload")

        if not script:
            return {
                "status": "no_script",
                "executed": False,
                "output": None,
                "error": "No fenced DataWeave script was found in the AI response.",
            }

        if input_payload is None:
            return {
                "status": "not_configured",
                "executed": False,
                "output": None,
                "error": "Provide context.input or context.inputPayload for DataWeave execution.",
            }

        if not isinstance(input_payload, str):
            input_payload = json.dumps(input_payload, ensure_ascii=False)

        return self.dw.execute(
            script,
            input_payload,
            context.get("inputMimeType", "application/json"),
        )

    def _user_prompt(self, message: str, context: dict) -> str:
        return (
            f"USER REQUEST:\n{message}\n\n"
            f"SUPPLIED CONTEXT:\n{json.dumps(context, default=str, indent=2)}\n\n"
            "RESPONSE RULES:\n"
            "- Answer the user's actual request directly.\n"
            "- Do not invent a different use case.\n"
            "- Do not add a generic Hello World example unless the user asks for it.\n"
            "- Do not create long assumption tables when the request is already clear.\n"
            "- If a requirement is genuinely ambiguous, ask one concise clarification "
            "or state the smallest necessary assumption.\n"
            "- Prefer concise, implementation-ready output.\n"
            "- For DataWeave, inspect the supplied input structure and use payload "
            "for the actual context.input value. Never invent payload.input unless "
            "the input JSON really contains an input field.\n"
            "- Put generated code in fenced blocks.\n"
            "- Never claim execution unless a real execution result is available."
        )

    def _repair_prompt(self, message: str, context: dict, answer: str, execution: dict) -> str:
        return (
            self._user_prompt(message, context)
            + "\n\nPREVIOUS ANSWER:\n"
            + answer
            + "\n\nREAL VALIDATION / EXECUTION FEEDBACK:\n"
            + json.dumps(execution, default=str, indent=2)
            + "\n\nRepair the answer using the exact feedback. Return the complete corrected artifact."
        )

    def _system_prompt(self, agent: str) -> str:
        prompts = {
            "dataweave": (
                "You are a senior MuleSoft DataWeave 2.0 engineer. Produce idiomatic, "
                "executable DW. The script will be run by a real DataWeave engine. "
                "Inspect the supplied payload before choosing fields. Consider nulls, "
                "arrays, objects, types, dates, reserved words, and edge cases. "
                "When execution fails, repair from the exact engine error."
            ),
            "mule-debugger": (
                "You are a senior MuleSoft production support engineer. Answer the "
                "specific error or operational question. Diagnose from evidence, "
                "separate facts from hypotheses, and give the smallest safe fix."
            ),
            "raml": (
                "You are a MuleSoft API architect. Answer the requested API contract "
                "directly. Produce valid RAML/OAS with reusable types, examples, "
                "validation, and consistent naming."
            ),
            "flow-builder": (
                "You are a senior MuleSoft integration architect. Build exactly the "
                "requested Mule flow using appropriate connectors, variables, error "
                "handling, and maintainable boundaries. Do not add unrelated flows."
            ),
            "munit": (
                "You are a senior MUnit engineer. Generate tests specifically for the "
                "provided Mule behavior, including success, failure, mocks, assertions, "
                "and relevant edge cases."
            ),
            "general-mulesoft": (
                "You are a senior MuleSoft engineer. Answer the user's exact question "
                "first. Be concise when the question is simple. For implementation "
                "requests, provide production-minded, copy-paste-ready guidance. "
                "Do not manufacture assumptions, unrelated examples, or extra sections "
                "unless they materially help answer the request."
            ),
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
