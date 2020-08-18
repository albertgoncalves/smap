#!/usr/bin/env bash

set -euxo pipefail

game_id=$1

curl "https://statsapi.web.nhl.com/api/v1/game/${game_id}/feed/live?site=en_nhl" \
    > "$WD/out/game_${game_id}.json"
