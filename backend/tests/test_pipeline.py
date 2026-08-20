import os

from app.pipeline import EngineeringPipeline


def test_offline_pipeline():
    os.environ["AI_PROVIDER"] = "offline"
    result = EngineeringPipeline().run("dataweave", "Create a transformation")
    assert result.attempts == 1
    assert result.verified is True
    assert result.validation == "pass"
