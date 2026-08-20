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
    """OpenAI-compatible client with Groq support and a small-model fallback."""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "mock").lower()
        self.api_key = os.getenv("AI_API_KEY", "")
        self.base_url = os.getenv(
            "AI_BASE_URL", "https://api.groq.com/openai/v1"
        ).rstrip("/")
        self.model = os.getenv("AI_MODEL", "openai/gpt-oss-120b")
        self.fallback_model = os.getenv(
            "AI_FALLBACK_MODEL", "llama-3.1-8b-instant"
        )
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "2048"))
        self.timeout = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        if self.provider in ("mock", "offline") or not self.api_key:
            return self._mock(user)

        try:
            return self._request(self.model, system, user, temperature)
        except LLMError as exc:
            # Groq applies model-specific token limits. If the large model is
            # exhausted, use the lightweight production model before failing.
            if (
                self.provider == "groq"
                and self.fallback_model
                and self.fallback_model != self.model
                and "HTTP 429" in str(exc)
            ):
                try:
                    return self._request(
                        self.fallback_model,
                        system,
                        user,
                        temperature,
                    )
                except LLMError as fallback_exc:
                    raise LLMError(
                        "AI provider rate limit reached for the primary and "
                        f"fallback models. Primary={self.model}; "
                        f"fallback={self.fallback_model}. "
                        "Wait for the provider limit to reset or configure "
                        "another provider/API key. "
                        f"Fallback detail: {fallback_exc}"
                    ) from fallback_exc
            raise

    def _request(
        self,
        model: str,
        system: str,
        user: str,
        temperature: float,
    ) -> str:
        payload = json.dumps({
            "model": model,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode("utf-8")

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
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(raw)
            except json.JSONDecodeError:
                detail = raw

            if exc.code == 429:
                raise LLMError(
                    f"AI provider request failed (HTTP 429) for model {model}: {detail}"
                ) from exc

            raise LLMError(
                f"AI provider request failed (HTTP {exc.code}): {detail}"
            ) from exc
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
            raise LLMError(f"AI provider request failed: {exc}") from exc

    def _mock(self, user: str) -> str:
        return (
            "Offline mode is active. Configure AI_PROVIDER and AI_API_KEY "
            "to enable model generation.\n\nRequest: " + user
        )
