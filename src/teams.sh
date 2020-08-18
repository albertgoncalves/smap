#!/usr/bin/env bash

set -euxo pipefail

curl "https://statsapi.web.nhl.com/api/v1/teams" > "$WD/out/teams.json"
