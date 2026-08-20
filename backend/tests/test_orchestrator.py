from app.orchestrator import Orchestrator


def test_dataweave_routing():
    result = Orchestrator().route("Create a DataWeave transformation")
    assert result.agent == "dataweave"
    assert "execute" in result.actions


def test_dataweave_natural_language_with_payload():
    result = Orchestrator().route(
        "Return customers whose salary is greater than 50000",
        {"input": [{"name": "Ravi", "salary": 75000}]},
    )
    assert result.agent == "dataweave"


def test_debug_routing():
    result = Orchestrator().route("Why is my Mule flow failing with an exception?")
    assert result.agent == "mule-debugger"
    assert "find_root_cause" in result.actions


def test_raml_routing():
    assert Orchestrator().route("Generate a RAML API contract").agent == "raml"


def test_munit_routing():
    assert Orchestrator().route("Generate MUnit test cases").agent == "munit"


def test_flow_routing():
    assert Orchestrator().route("Build a Mule XML flow").agent == "flow-builder"


def test_greeting_is_local_and_does_not_call_llm():
    result = Orchestrator().route("hi")
    assert result.validation == "conversation"
    assert result.verified is True
    assert "MuleSoft AI Copilot" in result.answer


def test_thanks_is_local():
    result = Orchestrator().route("thanks!")
    assert result.validation == "conversation"
    assert result.verified is True


def test_general_question_is_not_forced_into_dataweave():
    result = Orchestrator().route("What is API-led connectivity?")
    assert result.agent == "general-mulesoft"
