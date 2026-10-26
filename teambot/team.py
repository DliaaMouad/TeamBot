"""The TeamBot engine: single-seat answers and multi-seat huddles."""

from .context import BUSINESS_CONTEXT
from .llm import LLMError
from .roles import get_role, route


def _system_prompt(role):
    rules = "\n".join("- %s" % r for r in role.get("rules", []))
    return (
        "You are %s, %s on the founder's team.\n\n"
        "Role: %s\n\n"
        "Focus: %s\n\nVoice: %s\n\nStanding rules:\n%s\n\n"
        "Goal: %s\n\n"
        "Context:\n%s"
        % (role["name"], role["title"], role.get("role", ""),
           role.get("focus", ""), role.get("voice", ""), rules,
           role.get("goal", ""), BUSINESS_CONTEXT))


class Team:
    def __init__(self, roles, client):
        self.roles = roles
        self.client = client

    def ask(self, task, role_key=None):
        role = (get_role(self.roles, role_key) if role_key
                else route(self.roles, task))
        if role is None:
            return "Unknown role: %s" % role_key, None
        messages = [{"role": "system", "content": _system_prompt(role)},
                    {"role": "user", "content": task}]
        try:
            answer = self.client.chat(messages)
        except LLMError as exc:
            return "TeamBot stopped: %s" % exc, role
        header = "%s (%s)" % (role["name"], role["title"])
        return "%s:\n%s" % (header, answer), role

    def huddle(self, task, role_keys=None):
        """Each seat answers in turn, building on the previous ones,
        then the Chief of Staff synthesizes. Returns full transcript."""
        if role_keys:
            seats = [get_role(self.roles, k) for k in role_keys]
            seats = [s for s in seats if s is not None]
        else:
            seats = [r for r in self.roles if r["key"] != "chief"]
        transcript = []
        context = task
        for role in seats:
            messages = [{"role": "system",
                         "content": _system_prompt(role)},
                        {"role": "user",
                         "content": ("Task: %s\n\nWhat the team has "
                                     "said so far:\n%s"
                                     % (task, context))}]
            try:
                answer = self.client.chat(messages)
            except LLMError as exc:
                transcript.append("%s: stopped (%s)"
                                  % (role["name"], exc))
                break
            block = "%s (%s):\n%s" % (role["name"], role["title"],
                                      answer)
            transcript.append(block)
            context += "\n\n" + block
        chief = get_role(self.roles, "chief")
        if chief is not None:
            messages = [{"role": "system",
                         "content": _system_prompt(chief)},
                        {"role": "user",
                         "content": ("Synthesize this huddle into one "
                                     "short executive decision: the "
                                     "call, the next step, and the "
                                     "blocker.\n\nTask: %s\n\n%s"
                                     % (task, context))}]
            try:
                synthesis = self.client.chat(messages)
            except LLMError as exc:
                synthesis = "Synthesis stopped: %s" % exc
            transcript.append("SYNTHESIS (%s):\n%s"
                              % (chief["name"], synthesis))
        return "\n\n---\n\n".join(transcript)
