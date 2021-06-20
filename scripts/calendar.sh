#!/usr/bin/env bash

set -eux

date_start=$1
date_end=$2

curl "https://statsapi.web.nhl.com/api/v1/schedule?startDate=${date_start}&endDate=${date_end}" \
    > "${WD}/out/calendar_${date_start}_${date_end}.json"
