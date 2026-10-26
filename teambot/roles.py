"""Role loading and routing for TeamBot.

Roles come from roles.yaml, found in this order:
  1. TEAMBOT_ROLES, when set
  2. ./roles.yaml in the current directory (project-local config)
  3. roles.yaml next to the package (source checkout layout)
  4. roles.yaml inside the package (installed default)
If none of those load, a built-in fallback team is used.
"""

import os


FALLBACK_ROLES = [
    {"key": "chief", "name": "Ava", "title": "Chief of Staff",
     "focus": "Route work and synthesize answers.",
     "voice": "Blunt, calm, no fluff.",
     "rules": ["Never invent metrics.",
               "External sends are drafts only."],
     "keywords": []},
    {"key": "marketing", "name": "Mira", "title": "Marketing Lead",
     "focus": "LinkedIn content and campaigns.",
     "voice": "Sharp, founder-friendly.",
     "rules": ["No links in post bodies.",
               "Posting stays manual."],
     "keywords": ["linkedin", "post", "content", "marketing"]},
    {"key": "operations", "name": "Otto", "title": "Operations Lead",
     "focus": "Plans, processes, checklists.",
     "voice": "Structured, concrete.",
     "rules": ["Every plan names day, block, and outcome."],
     "keywords": ["operations", "plan", "week", "process"]},
    {"key": "partnerships", "name": "Pia", "title": "Partnerships Lead",
     "focus": "Bank partners and outreach.",
     "voice": "Warm, precise, research-first.",
     "rules": ["Outreach drafts are text only.",
               "Nothing sends alone."],
     "keywords": ["partner", "bank", "pilot", "outreach"]},
    {"key": "fundraising", "name": "Finn", "title": "Fundraising Strategist",
     "focus": "Decks, investors, round strategy.",
     "voice": "Direct, evidence-first.",
     "rules": ["Never invent traction.",
               "Mark gaps as [FILL]."],
     "keywords": ["fundraising", "investor", "deck", "pitch"]},
]


def _parse_yaml(text):
    """Minimal parser for the roles.yaml shape: a list of mappings
    with scalar values and one inline list per role (keywords)."""
    roles, current = [], None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("- key:"):
            current = {"keywords": []}
            roles.append(current)
            current["key"] = line.split(":", 1)[1].strip()
            continue
        if current is None:
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key == "keywords":
            items = value.strip("[]")
            current["keywords"] = [i.strip() for i in items.split(",")
                                   if i.strip()]
        elif key == "rules":
            current["rules"] = []
        elif line.startswith("    - ") and "rules" in current:
            current["rules"].append(line.strip()[2:].strip())
        else:
            current[key] = value
    return [r for r in roles if r.get("key")]


def load_roles(path=None):
    if path is not None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                roles = _parse_yaml(f.read())
        except (OSError, ValueError):
            roles = []
        return roles or list(FALLBACK_ROLES)
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.environ.get("TEAMBOT_ROLES", ""),
        os.path.join(os.getcwd(), "roles.yaml"),
        os.path.join(os.path.dirname(here), "roles.yaml"),
        os.path.join(here, "roles.yaml"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                roles = _parse_yaml(f.read())
        except (OSError, ValueError):
            continue
        if roles:
            return roles
    return list(FALLBACK_ROLES)


def get_role(roles, key):
    for role in roles:
        if role["key"] == key:
            return role
    return None


def route(roles, task):
    """Pick the best seat for a task by keyword. Falls back to chief."""
    lowered = task.lower()
    best, best_hits = None, 0
    for role in roles:
        if role["key"] == "chief":
            continue
        hits = sum(1 for kw in role.get("keywords", [])
                   if kw in lowered)
        if hits > best_hits:
            best, best_hits = role, hits
    if best is None:
        return get_role(roles, "chief")
    return best
