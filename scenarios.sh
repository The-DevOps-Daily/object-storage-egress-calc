#!/usr/bin/env bash
# The four workloads used in the post. Output is recorded in runs/scenarios.txt.
set -euo pipefail
cd "$(dirname "$0")"
run() { echo "## $1"; shift; echo "\$ python3 calc.py $*"; python3 calc.py "$@"; echo; }
{
run "Downloads site: small bucket, a lot of traffic" --storage-gb 500 --egress-gb 5000 --gets 20000000 --puts 10000
run "Backups: big bucket, rare restores, 30-day retention" --storage-gb 10000 --egress-gb 200 --gets 100000 --puts 1000000 --lifetime-days 30
run "Media: heavy egress, many reads" --storage-gb 2000 --egress-gb 50000 --gets 100000000 --puts 100000
run "Side project" --storage-gb 50 --egress-gb 200 --gets 1000000 --puts 10000
} | tee runs/scenarios.txt
