"""TeamBot command line interface.

Commands:
  ask TASK [--role KEY] [--mock]
      Ask the team. Without --role, the task is routed to the best seat.
  huddle TASK [--roles a,b] [--mock]
      Every seat answers in turn, then the Chief of Staff synthesizes.
  roles
      List the team and their seats. Edit roles.yaml to customize.
  briefing [--mock]
      One highest-leverage action per seat, for the day ahead.
  serve [--port 8787] [--mock]
      Local web app on http://127.0.0.1:8787. The browser never sees
      the API key; the server calls the provider with TEAMBOT_API_KEY.

Everything the team produces is a draft. Nothing external is ever
sent without the founder's explicit approval.
"""

import argparse
import sys

from .llm import Config, MockClient, OpenAICompatibleClient
from .roles import load_roles
from .team import Team

BRIEFING_PROMPT = ("What is the single highest-leverage action for your "
                   "area today, and what is the one thing that would "
                   "block it? Answer in under 80 words.")


def _team(config, roles_path=None):
    roles = load_roles(roles_path)
    client = MockClient() if config.mock else OpenAICompatibleClient(config)
    return Team(roles, client)


def cmd_ask(args, config):
    problem = config.validate()
    if problem:
        print(problem, file=sys.stderr)
        return 2
    team = _team(config, args.roles_file)
    answer, _role = team.ask(args.task, role_key=args.role)
    print(answer)
    return 0


def cmd_huddle(args, config):
    problem = config.validate()
    if problem:
        print(problem, file=sys.stderr)
        return 2
    team = _team(config, args.roles_file)
    keys = args.roles.split(",") if args.roles else None
    print(team.huddle(args.task, role_keys=keys))
    return 0


def cmd_roles(args, config):
    roles = load_roles(args.roles_file)
    for role in roles:
        print("%s: %s (%s)" % (role["key"], role["name"],
                               role["title"]))
        print("   %s" % role.get("focus", ""))
        if role.get("goal"):
            print("   Goal: %s" % role["goal"])
        if role.get("avatar"):
            print("   avatar: %s" % role["avatar"])
    print("\nCustomize: edit roles.yaml, or set TEAMBOT_ROLES to its path.")
    return 0


def cmd_briefing(args, config):
    problem = config.validate()
    if problem:
        print(problem, file=sys.stderr)
        return 2
    team = _team(config, args.roles_file)
    for role in team.roles:
        answer, _ = team.ask(BRIEFING_PROMPT, role_key=role["key"])
        print(answer)
        print()
    return 0


def cmd_serve(args, config):
    from .server import run_server
    run_server(port=args.port, demo=getattr(args, "mock", False))
    return 0


def _shared(p):
    p.add_argument("--model", default=argparse.SUPPRESS)
    p.add_argument("--base-url", default=argparse.SUPPRESS)
    p.add_argument("--mock", action="store_true",
                   default=argparse.SUPPRESS,
                   help="deterministic output, no key needed")
    p.add_argument("--roles-file", default=None,
                   help="path to a custom roles.yaml")
    return p


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="teambot",
        description="TeamBot: a 10-seat AI team for one founder.")
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--mock", action="store_true",
                        help="deterministic output, no key needed")
    sub = parser.add_subparsers(dest="command", required=True)

    p = _shared(sub.add_parser("ask", help="ask the team"))
    p.add_argument("task")
    p.add_argument("--role", default=None, help="seat key, e.g. marketing")
    p.set_defaults(fn=cmd_ask)

    p = _shared(sub.add_parser("huddle", help="multi-seat huddle"))
    p.add_argument("task")
    p.add_argument("--roles", default=None,
                   help="comma-separated seat keys")
    p.set_defaults(fn=cmd_huddle)

    p = _shared(sub.add_parser("roles", help="list the team"))
    p.set_defaults(fn=cmd_roles)

    p = _shared(sub.add_parser("briefing", help="one action per seat"))
    p.set_defaults(fn=cmd_briefing)

    p = _shared(sub.add_parser("serve", help="local web app"))
    p.add_argument("--port", type=int, default=8787)
    p.set_defaults(fn=cmd_serve)

    args = parser.parse_args(argv)
    config = Config(model=getattr(args, "model", None),
                    base_url=getattr(args, "base_url", None),
                    mock=getattr(args, "mock", False))
    return args.fn(args, config)


if __name__ == "__main__":
    sys.exit(main())
