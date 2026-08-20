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
        normalized = text.lower()
        context = context or {}

        # Greetings are conversation, not engineering tasks. Keep them local
        # so a simple "hi" never consumes model tokens or generates assumptions.
        if self._is_greeting(normalized):
            return AgentResult(
                agent="general-mulesoft",
                answer=(
                    "Hi! 👋 I’m your MuleSoft AI Copilot.\n\n"
                    "Ask me anything about DataWeave, Mule flows, APIs/RAML, "
                    "MUnit, debugging, connectors, SQL, deployments, or "
                    "end-to-end integrations."
                ),
                confidence=1.0,
                actions=["greeting"],
                verified=True,
                attempts=0,
                validation="greeting",
            )

        dataweave_terms = (
            "dataweave", "%dw", "transform", "transformation", "mapping",
            "map ", "filter", "group by", "groupby", "group customers",
            "sort", "order by", "distinct", "pluck", "mapobject", "reduce",
            "flatten", "flatmap", "join", "merge", "rename", "remove null",
            "exclude null", "missing fields", "calculate", "average", "avg",
            "sum", "count", "min", "max", "conditional", "if else",
            "convert json", "json to xml", "xml to json", "json to csv",
            "csv to json", "payload", "field", "fields", "extract",
            "return the names", "return names", "customers",
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
            "error", "exception", "failed", "failure", "stack trace",
            "why is", "not working", "doesn't work", "does not work",
            "timeout", "401", "403", "404", "405", "429", "500",
            "null pointer", "cannot coerce", "deployment issue", "ci failed",
            "build failed", "runtime error", "connector error",
        )
        flow_terms = (
            "mule xml", "mule flow", "flow", "subflow", "connector",
            "http listener", "http request", "sftp", "salesforce", "snowflake",
            "database connector", "mq", "jms", "s3", "scatter gather",
            "choice router", "foreach", "until successful", "error handler",
            "try scope", "scheduler", "batch job", "file transfer",
        )
        sql_terms = (
            "sql", "snowflake query", "select ", "insert ", "update ",
            "delete ", "merge into", "stored procedure", "database query",
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
            )
        ):
            agent = "dataweave"
        else:
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
    def _is_greeting(text: str) -> bool:
        if not text:
            return False
        cleaned = " ".join(text.split()).strip("!?.,:;-")
        greetings = {
            "hi", "hello", "hey", "hiya", "howdy", "namaste",
            "good morning", "good afternoon", "good evening", "good night",
            "hi there", "hello there", "hey there",
        }
        return cleaned in greetings
