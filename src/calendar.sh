#!/usr/bin/env bash

set -euxo pipefail

team_id=$1
date_start=$2
date_end=$3

curl "https://statsapi.web.nhl.com/api/v1/schedule?teamId=${team_id}&startDate=${date_start}&endDate=${date_end}" \
    > "$WD/out/calendar_${team_id}_${date_start}_${date_end}.json"
