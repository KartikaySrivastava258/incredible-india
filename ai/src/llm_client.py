"""LLM Client for communicating with Ollama."""
import json
import requests
from typing import Dict, Any, Optional
from .config import LLM_BASE_URL, LLM_MODEL


class LLMClient:
    """Client for interacting with local LLM via Ollama."""

    def __init__(self, base_url: str = LLM_BASE_URL, model: str = LLM_MODEL):
        self.base_url = base_url.rstrip('/')
        self.model = model

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")

    def generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Generate a JSON response from the LLM with retry logic."""
        # First attempt
        try:
            text = self.generate(prompt, system)
            return self._extract_json(text)
        except (json.JSONDecodeError, ValueError) as e:
            # Retry once with explicit JSON instruction
            retry_prompt = f"{prompt}\n\nIMPORTANT: Respond with ONLY valid JSON, no other text."
            try:
                text = self.generate(retry_prompt, system)
                return self._extract_json(text)
            except (json.JSONDecodeError, ValueError):
                # Return a partial fallback structure
                return {"error": "malformed_json", "raw_text": text}

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text."""
        # Try to find JSON within code blocks
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()

        return json.loads(text.strip())


# Mock client for testing
class MockLLMClient(LLMClient):
    """Mock LLM client for testing without Ollama."""

    def __init__(self):
        super().__init__()
        self.responses = []
        self.call_count = 0

    def set_responses(self, responses):
        """Set canned responses for testing."""
        self.responses = responses
        self.call_count = 0

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Return canned response."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return "मुझे समझ नहीं आया। कृपया फिर से बताएं।"

    def generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Return canned JSON response."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            if isinstance(response, dict):
                return response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"error": "malformed_json", "raw_text": response}
        return {}
