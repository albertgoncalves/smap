#!/usr/bin/env bash

set -eux

curl "https://statsapi.web.nhl.com/api/v1/teams" > "$WD/out/teams.json"
