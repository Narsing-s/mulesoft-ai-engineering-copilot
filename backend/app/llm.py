import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

# Load backend/.env regardless of the directory from which Uvicorn is started.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class LLMError(RuntimeError):
    pass


class LLMClient:
    """OpenAI-compatible client with Groq support and an offline mock fallback."""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "mock").lower()
        self.api_key = os.getenv("AI_API_KEY", "")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        self.model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        if self.provider in ("mock", "offline") or not self.api_key:
            return self._mock(user)

        payload = json.dumps({
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode())
            return body["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
            raise LLMError(f"AI provider request failed: {exc}") from exc

    def _mock(self, user: str) -> str:
        return "Offline mode is active. Configure AI_PROVIDER=groq and AI_API_KEY to enable model generation.\n\nRequest: " + user
