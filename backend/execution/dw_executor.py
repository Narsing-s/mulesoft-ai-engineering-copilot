import json
import os
import urllib.error
import urllib.request


class DataWeaveExecutor:
    """Call the configured trusted DataWeave execution service."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("DW_EXECUTOR_URL", "")).rstrip("/")

    @property
    def available(self) -> bool:
        return bool(self.base_url)

    def execute(self, script: str, input_payload: str, input_mime: str = "application/json") -> dict:
        if not self.available:
            return {
                "status": "not_configured",
                "executed": False,
                "output": None,
                "error": "DW_EXECUTOR_URL is not configured",
            }

        body = json.dumps({
            "dataweave": script,
            "input": input_payload,
            "inputMimeType": input_mime,
        }).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/api/v1/dataweave/test",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
                try:
                    output = json.loads(raw)
                except json.JSONDecodeError:
                    output = {"raw": raw}
                return {"status": "executed", "executed": True, "output": output, "error": None}
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            return {"status": "execution_error", "executed": False, "output": None, "error": str(exc)}
