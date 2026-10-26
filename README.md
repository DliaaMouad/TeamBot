# TeamBot

A customizable AI team for one founder, in the terminal and on the
web. Pure Python standard library. No dependencies, no build step.

Ten seats with distinct roles, keyword routing, multi-seat huddles,
and a daily briefing. It talks to any OpenAI-compatible API
(OpenRouter by default) and works fully offline in demo mode.

## Seats

| Seat | Name | Does |
| --- | --- | --- |
| Chief of Staff | Ava | Routes work, synthesizes huddles |
| Marketing Lead | Mira | Content, campaigns, brand voice |
| Operations Lead | Otto | Weekly plans, processes, checklists |
| Partnerships Lead | Pia | Partners, outreach, deal memos |
| Fundraising Strategist | Finn | Decks, investors, round strategy |
| Chief Product Officer | Cleo | Roadmaps, launches, what to build next |
| Head of Sales | Sam | Pipeline, demos, closing paid work |
| Chief Financial Officer | Iris | Runway, burn, pricing, round math |
| Co-founder | Leo | Pressure-tests ideas, spots the flaw |
| Chief Executive Officer | Max | Vision, priorities, hard calls |

Each seat carries a first-person role statement, standing rules, and
a goal, all of which go into that seat's prompt.

## Requirements

Python 3.10 or newer. Nothing to install.

## Install it like a real app

```sh
git clone https://github.com/DliaaMouad/TeamBot.git
cd teambot
pip install .
teambot roles
```

That puts a `teambot` command on your path. Or run it from the
checkout without installing:

```sh
sh teambot.sh roles
```

Note: the file loses its executable bit on GitHub, so `sh` is the
reliable form. Running `chmod +x teambot.sh` once, then `./teambot.sh`,
works too.

## Web app on localhost

```sh
teambot serve
```

Then open http://127.0.0.1:8787 in a browser. You get the full team
as a chat app: seat picker with each seat's role, rules, and goal,
Huddle mode, Morning Briefing, and per-answer Copy buttons. The
browser never sees your API key; the server calls the provider with
the key from the environment. Use `--port` to change the port and
`--mock` (or the Demo toggle in the UI) to try it with no key.

## Real answers

Set an API key (OpenRouter by default):

```sh
export TEAMBOT_API_KEY="your key"
teambot ask "plan my week"
```

Optional: `TEAMBOT_BASE_URL` and `TEAMBOT_MODEL` for any
OpenAI-compatible endpoint, or pass `--model` / `--base-url` per call.

## Commands

```sh
teambot ask "write a launch post"          # routed to the best seat
teambot ask "check our runway" --role cfo  # a specific seat
teambot huddle "should we raise prices"    # every seat, then Ava synthesizes
teambot huddle "launch plan" --roles marketing,operations
teambot briefing                          # one action per seat
teambot roles                             # list the team
teambot serve                             # local web app
```

Add `--mock` to any command for deterministic demo answers with no key.

## Customize

Edit `roles.yaml` to change a seat's role, focus, voice, rules, goal,
or keywords, or to add a new seat. Keywords drive automatic routing
when no `--role` is given. TeamBot looks for roles in this order:
`TEAMBOT_ROLES` when set, `./roles.yaml` in the current directory,
`roles.yaml` next to the package, then the copy shipped inside the
package.

Edit `teambot/context.py` to give the team your shared business
context, so you never re-explain your work. The shipped file is a
template with example entries only.

The `avatar` field on a seat is optional decoration; the terminal
prints the path in `roles` output, and the web app shows the image
when the file exists, falling back to a colored initial otherwise.

## Safety rules

Everything the team produces is a draft. Nothing external is ever
sent without the founder's explicit approval. The team never invents
metrics, traction, commitments, or contacts, and marks gaps as
`[FILL]`. API keys come from the environment at runtime and are never
written to disk.

## Tests

```sh
python3 -m unittest discover -s tests
```

## License

MIT. See `LICENSE`.
