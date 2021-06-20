#!/usr/bin/env bash

set -eux

game_id=$1
game_json="${WD}/out/game_${game_id}.json"

curl "https://statsapi.web.nhl.com/api/v1/game/${game_id}/feed/live?site=en_nhl" \
    > "${game_json}"
echo "${game_json}"
