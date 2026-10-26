#!/bin/sh
# TeamBot launcher: run from any directory.
# Usage: /path/to/teambot/teambot.sh ask "plan my week"
#        /path/to/teambot/teambot.sh huddle "launch the pilot push"
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m teambot "$@"
