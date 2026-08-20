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
    """Route natural-language MuleSoft requests to the right engineering agent."""

    def __init__(self):
        self.pipeline = EngineeringPipeline()

    def route(self, message: str, context: dict | None = None) -> AgentResult:
        text = (message or "").strip()
        normalized = " ".join(text.lower().split())
        context = context or {}

        # Conversation must never consume an AI request. This also prevents a
        # greeting from being interpreted as an engineering task.
        conversation = self._conversation_response(normalized)
        if conversation is not None:
            return AgentResult(
                agent="general-mulesoft",
                answer=conversation,
                confidence=1.0,
                actions=["conversation"],
                verified=True,
                attempts=0,
                validation="conversation",
            )

        dataweave_terms = (
            "dataweave", "%dw", "transform", "transformation", "mapping",
            "map ", "map over", "filter", "group by", "groupby", "grouped",
            "sort", "distinct", "pluck", "mapobject", "reduce", "flatten",
            "flatmap", "join", "merge", "rename", "remove null", "exclude null",
            "missing fields", "calculate", "average", "avg", "sum", "count",
            "min", "max", "conditional", "if else", "convert json", "json to xml",
            "xml to json", "json to csv", "csv to json", "extract", "transform payload",
            "filter records", "map fields", "group customers", "return names",
        )
        munit_terms = (
            "munit", "unit test", "test case", "assert that", "mock when",
            "verify call", "test suite", "coverage",
        )
        raml_terms = (
            "raml", "api spec", "api specification", "openapi", "oas",
            "api contract", "resource type", "trait", "schema definition",
        )
        debug_terms = (
            "error", "exception", "failed", "failure", "stack trace", "why is",
            "not working", "doesn't work", "does not work", "timeout", "401", "403",
            "404", "405", "429", "500", "null pointer", "cannot coerce",
            "deployment issue", "ci failed", "build failed", "runtime error",
            "connector error", "why am i getting", "fix this error", "troubleshoot",
        )
        flow_terms = (
            "mule xml", "mule flow", "subflow", "http listener", "http request",
            "sftp", "salesforce", "snowflake", "database connector", "mq", "jms", "s3",
            "scatter gather", "choice router", "foreach", "until successful",
            "error handler", "try scope", "scheduler", "batch job", "file transfer",
        )
        sql_terms = (
            "sql", "snowflake query", "select ", "insert ", "update ", "delete ",
            "merge into", "stored procedure", "database query",
        )

        requested_tool = str(context.get("tool", "auto")).lower()
        forced = {
            "dataweave": "dataweave",
            "debug": "mule-debugger",
            "raml": "raml",
            "flow": "flow-builder",
            "munit": "munit",
            "sql": "general-mulesoft",
        }

        if requested_tool in forced:
            agent = forced[requested_tool]
        elif any(term in normalized for term in munit_terms):
            agent = "munit"
        elif any(term in normalized for term in raml_terms):
            agent = "raml"
        # Explicit debugging wins when the user is asking why/fixing a failure.
        elif any(term in normalized for term in debug_terms):
            agent = "mule-debugger"
        elif any(term in normalized for term in flow_terms):
            agent = "flow-builder"
        elif any(term in normalized for term in sql_terms) and not any(
            term in normalized for term in dataweave_terms
        ):
            agent = "general-mulesoft"
        elif any(term in normalized for term in dataweave_terms):
            agent = "dataweave"
        elif context.get("input") is not None and any(
            verb in normalized for verb in (
                "return", "create", "convert", "extract", "group", "filter",
                "calculate", "transform", "map", "sort", "remove", "rename",
                "select", "reshape", "aggregate", "flatten",
            )
        ):
            agent = "dataweave"
        else:
            # Do not guess an engineering agent. The general model receives
            # the exact user question and answers that question directly.
            agent = "general-mulesoft"

        metadata = {
            "dataweave": (0.96, ["analyze_contract", "generate_dw", "execute_dw", "validate", "self_repair"]),
            "munit": (0.90, ["inspect_flow", "derive_cases", "generate_munit", "validate_tests"]),
            "raml": (0.90, ["extract_contract", "generate_raml", "validate_spec"]),
            "mule-debugger": (0.94, ["classify_error", "analyze_context", "find_root_cause", "propose_fix", "validate_fix"]),
            "flow-builder": (0.91, ["extract_requirements", "design_flow", "generate_xml", "validate_xml"]),
            "general-mulesoft": (0.78, ["analyze_request", "generate_solution", "validate"]),
        }
        confidence, actions = metadata[agent]

        result = self.pipeline.run(agent, text, context)
        return AgentResult(
            agent,
            result.answer,
            confidence,
            actions,
            result.verified,
            result.attempts,
            result.validation,
        )

    @staticmethod
    def _conversation_response(text: str) -> str | None:
        cleaned = text.strip("!?.,:;-")
        greetings = {
            "hi", "hello", "hey", "hiya", "howdy", "namaste",
            "good morning", "good afternoon", "good evening", "good night",
            "hi there", "hello there", "hey there",
        }
        if cleaned in greetings:
            return (
                "Hi! 👋 I’m your MuleSoft AI Copilot.\n\n"
                "Ask me anything about DataWeave, Mule flows, APIs/RAML, "
                "MUnit, debugging, connectors, SQL, CloudHub, or end-to-end integrations."
            )

        if cleaned in {"thanks", "thank you", "thx", "thanks a lot"}:
            return "You're welcome! 👋 Send me your next MuleSoft requirement whenever you're ready."

        if cleaned in {"who are you", "what are you"}:
            return (
                "I’m MuleSoft AI Copilot — an engineering assistant for DataWeave, "
                "Mule 4 flows, APIs/RAML, MUnit, debugging, connectors, SQL and deployments."
            )

        if cleaned in {"what can you do", "what do you do", "help", "help me"}:
            return (
                "I can help you build and troubleshoot MuleSoft solutions. "
                "For DataWeave, I can generate the script and, when you provide an input payload, "
                "execute and verify it against the real DataWeave engine."
            )

        return None
