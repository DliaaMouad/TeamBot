"""Tests for the TeamBot local web app (no network, no API key)."""

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from teambot.llm import Config, OpenAICompatibleClient
from teambot.roles import load_roles
from teambot.server import create_server
from teambot.team import Team


def _call(port, method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = request.Request("http://127.0.0.1:%d%s" % (port, path),
                          data=data, method=method,
                          headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except request.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


class TestServerEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(0, demo=True)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_index_serves_html(self):
        req = request.Request("http://127.0.0.1:%d/" % self.port)
        with request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            self.assertIn("TeamBot", r.read().decode("utf-8"))

    def test_seats(self):
        code, seats = _call(self.port, "GET", "/api/seats")
        self.assertEqual(code, 200)
        self.assertEqual(len(seats), 10)
        self.assertTrue(all(s.get("goal") for s in seats))

    def test_ask_demo(self):
        code, out = _call(self.port, "POST", "/api/ask",
                          {"task": "plan my week", "demo": True})
        self.assertEqual(code, 200)
        self.assertIn("Otto", out["answer"])

    def test_huddle_demo(self):
        code, out = _call(self.port, "POST", "/api/huddle",
                          {"task": "launch plan", "demo": True,
                           "roles": ["marketing", "operations"]})
        self.assertEqual(code, 200)
        self.assertIn("SYNTHESIS", out["transcript"])

    def test_ask_needs_task(self):
        code, out = _call(self.port, "POST", "/api/ask", {"task": ""})
        self.assertEqual(code, 400)


class FakeUpstream(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        data = json.dumps({"choices": [{"message": {
            "content": "Canned answer from upstream."}}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class TestRealClientPath(unittest.TestCase):
    """The non-mock client path, against a local fake provider."""

    def test_live_client_round_trip(self):
        upstream = ThreadingHTTPServer(("127.0.0.1", 0), FakeUpstream)
        port = upstream.server_address[1]
        thread = threading.Thread(target=upstream.serve_forever,
                                  daemon=True)
        thread.start()
        try:
            config = Config(base_url="http://127.0.0.1:%d" % port)
            config.api_key = "test-key"
            team = Team(load_roles(), OpenAICompatibleClient(config))
            answer, role = team.ask("hello", role_key="chief")
            self.assertIn("Canned answer from upstream.", answer)
            self.assertEqual(role["key"], "chief")
        finally:
            upstream.shutdown()
            upstream.server_close()


if __name__ == "__main__":
    unittest.main()
