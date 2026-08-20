from app.orchestrator import Orchestrator


def test_dataweave_routing():
    result = Orchestrator().route("Create a DataWeave transformation")
    assert result.agent == "dataweave"
    assert "execute" in result.actions


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
