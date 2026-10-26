"""TeamBot local web app: the team on localhost.

Run: ./teambot.sh serve [--port 8787] [--mock]
Then open http://127.0.0.1:8787 in a browser.

The browser never sees the API key. The server calls the provider
with the key from the environment (TEAMBOT_API_KEY). With --mock, or
with the Demo toggle in the UI, answers come from the deterministic
mock client instead, so no key is needed to try it.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .agent import BRIEFING_PROMPT
from .llm import Config, MockClient, OpenAICompatibleClient
from .roles import load_roles
from .team import Team

DEFAULT_PORT = 8787


def _team(demo):
    """Fresh team per request, so roles.yaml edits apply live."""
    roles = load_roles()
    if demo:
        return Team(roles, MockClient()), None
    config = Config()
    problem = config.validate()
    if problem:
        return None, problem
    return Team(roles, OpenAICompatibleClient(config)), None


def _seat_json(role):
    return {
        "key": role["key"],
        "name": role["name"],
        "title": role["title"],
        "focus": role.get("focus", ""),
        "role": role.get("role", ""),
        "rules": role.get("rules", []),
        "goal": role.get("goal", ""),
        "avatar": role.get("avatar", ""),
    }


def _web_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "web")


def _avatars_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "avatars")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            index = os.path.join(_web_dir(), "index.html")
            if not os.path.isfile(index):
                self._json(500, {"error": "web UI is not installed"})
                return
            with open(index, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/seats":
            self._json(200, [_seat_json(r) for r in load_roles()])
        elif path == "/api/status":
            config = Config()
            self._json(200, {"has_key": bool(config.api_key),
                             "demo_default": bool(
                                 getattr(self.server, "demo", False))})
        elif path.startswith("/avatars/"):
            name = os.path.basename(path)
            if not name.endswith(".webp") or "/" in name:
                self._json(404, {"error": "not found"})
                return
            full = os.path.join(_avatars_dir(), name)
            if not os.path.isfile(full):
                self._json(404, {"error": "not found"})
                return
            with open(full, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/webp")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()
        if body is None:
            self._json(400, {"error": "invalid JSON"})
            return
        if path == "/api/ask":
            task = (body.get("task") or "").strip()
            if not task:
                self._json(400, {"error": "task is required"})
                return
            demo = bool(body.get("demo") or
                        getattr(self.server, "demo", False))
            team, problem = _team(demo)
            if problem:
                self._json(400, {"error": problem})
                return
            answer, role = team.ask(task, role_key=body.get("role"))
            self._json(200, {"answer": answer,
                             "role": _seat_json(role) if role else None})
        elif path == "/api/huddle":
            task = (body.get("task") or "").strip()
            if not task:
                self._json(400, {"error": "task is required"})
                return
            demo = bool(body.get("demo") or
                        getattr(self.server, "demo", False))
            team, problem = _team(demo)
            if problem:
                self._json(400, {"error": problem})
                return
            keys = body.get("roles")
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.split(",") if k.strip()]
            self._json(200, {"transcript": team.huddle(task,
                                                      role_keys=keys)})
        elif path == "/api/briefing":
            demo = bool(body.get("demo") or
                        getattr(self.server, "demo", False))
            team, problem = _team(demo)
            if problem:
                self._json(400, {"error": problem})
                return
            items = []
            for role in team.roles:
                answer, _ = team.ask(BRIEFING_PROMPT,
                                     role_key=role["key"])
                items.append({"key": role["key"], "name": role["name"],
                              "title": role["title"], "answer": answer})
            self._json(200, {"items": items})
        else:
            self._json(404, {"error": "not found"})


def create_server(port=DEFAULT_PORT, demo=False):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.demo = demo
    return server


def run_server(port=DEFAULT_PORT, demo=False):
    server = create_server(port, demo)
    print("TeamBot running at http://127.0.0.1:%d" % port)
    if demo:
        print("Demo mode: answers are placeholders, no key needed.")
    else:
        print("Using TEAMBOT_API_KEY from the environment.")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTeamBot stopped.")
