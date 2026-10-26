"""Tests for TeamBot (no network, no API key needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from teambot.llm import MockClient
from teambot.roles import get_role, load_roles, route
from teambot.team import Team


class TestRoles(unittest.TestCase):
    def setUp(self):
        self.roles = load_roles()

    def test_ten_seats(self):
        keys = {r["key"] for r in self.roles}
        self.assertEqual(keys, {"chief", "marketing", "operations",
                                "partnerships", "fundraising",
                                "cpo", "sales", "cfo", "cofounder",
                                "ceo"})

    def test_routing(self):
        self.assertEqual(route(self.roles, "write a linkedin post")["key"],
                         "marketing")
        self.assertEqual(route(self.roles, "plan my week")["key"],
                         "operations")
        self.assertEqual(route(self.roles, "draft a bank intro")["key"],
                         "partnerships")
        self.assertEqual(route(self.roles, "review my deck")["key"],
                         "fundraising")
        self.assertEqual(route(self.roles, "set the product roadmap")["key"],
                         "cpo")
        self.assertEqual(route(self.roles, "build the sales pipeline")["key"],
                         "sales")
        self.assertEqual(route(self.roles, "check our runway")["key"],
                         "cfo")
        self.assertEqual(route(self.roles, "hello")["key"], "chief")

    def test_every_seat_has_role_and_goal(self):
        for role in self.roles:
            self.assertTrue(role.get("role"), role["key"])
            self.assertTrue(role.get("goal"), role["key"])
            self.assertIn("founder", role["role"].lower(), role["key"])
            for personal in ("Mouad", "Duck", "Raise", "Aurium",
                             "MarsLabs"):
                self.assertNotIn(personal, role["role"])

    def test_unknown_role(self):
        self.assertIsNone(get_role(self.roles, "nope"))


class TestTeam(unittest.TestCase):
    def setUp(self):
        self.team = Team(load_roles(), MockClient())

    def test_ask_single_seat(self):
        answer, role = self.team.ask("write a linkedin post",
                                     role_key="marketing")
        self.assertEqual(role["key"], "marketing")
        self.assertIn("Mira", answer)

    def test_ask_routed(self):
        answer, role = self.team.ask("plan my week")
        self.assertEqual(role["key"], "operations")

    def test_huddle_covers_seats_and_synthesis(self):
        text = self.team.huddle("launch the pilot push",
                                role_keys=["marketing", "operations"])
        self.assertIn("Mira", text)
        self.assertIn("Otto", text)
        self.assertIn("SYNTHESIS", text)

    def test_business_context_present(self):
        from teambot.context import BUSINESS_CONTEXT
        for word in ("founder", "Standing rules"):
            self.assertIn(word, BUSINESS_CONTEXT)

    def test_prompt_carries_role_and_goal(self):
        from teambot.team import _system_prompt
        role = get_role(load_roles(), "chief")
        prompt = _system_prompt(role)
        self.assertIn("Role: I'm the Chief of Staff for the founder.", prompt)
        self.assertIn("Standing rules:", prompt)
        self.assertIn("Goal: Keep the founder's week focused", prompt)


class TestPackagedRoles(unittest.TestCase):
    def test_packaged_copy_has_ten_seats(self):
        import teambot
        pkg = os.path.join(os.path.dirname(teambot.__file__),
                           "roles.yaml")
        self.assertEqual(len(load_roles(pkg)), 10)


if __name__ == "__main__":
    unittest.main()
