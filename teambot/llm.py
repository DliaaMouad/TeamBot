"""LLM client for TeamBot: OpenAI-compatible API, plus a mock.

Configuration from the environment at runtime:
TEAMBOT_API_KEY, TEAMBOT_BASE_URL, TEAMBOT_MODEL. Nothing secret is written to disk.
"""

import json
import os
import urllib.error
import urllib.request


class LLMError(Exception):
    pass


def _env(*names):
    for name in names:
        value = os.environ.get(name, "")
        if value:
            return value
    return ""


class Config:
    def __init__(self, model=None, base_url=None, mock=False):
        self.api_key = _env("TEAMBOT_API_KEY")
        self.base_url = (base_url or _env("TEAMBOT_BASE_URL") or
                         "https://openrouter.ai/api/v1")
        self.model = model or _env("TEAMBOT_MODEL") or "openai/gpt-4o"
        self.mock = mock

    def validate(self):
        if self.mock:
            return None
        if not self.api_key:
            return ("No API key found. Set TEAMBOT_API_KEY in your environment.")
        return None


class OpenAICompatibleClient:
    def __init__(self, config):
        self.config = config

    def chat(self, messages):
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {"model": self.config.model, "messages": messages}
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer %s" % self.config.api_key},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise LLMError("API error %s" % exc.code)
        except urllib.error.URLError as exc:
            raise LLMError("network error: %s" % exc)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise LLMError("unexpected API response")


class MockClient:
    """Deterministic stand-in. Answers in the voice of the seat."""

    def chat(self, messages):
        seat = "the team"
        task = ""
        for msg in messages:
            if msg["role"] == "system" and "You are " in msg["content"]:
                seat = msg["content"].split("You are ", 1)[1].split(
                    ",", 1)[0].split("\n", 1)[0]
            if msg["role"] == "user":
                task = msg["content"]
        snippet = task[:80]
        if len(task) > 80 and " " in snippet:
            snippet = snippet.rsplit(" ", 1)[0] + "..."
        return ("[%s, mock] On '%s': here is the plan. First, the "
                "sharp version of the problem in one line. Second, "
                "the three moves that matter, in order. Third, the "
                "one next step and what would block it. Nothing "
                "external is sent; this is a draft for the founder to "
                "approve." % (seat, snippet))
