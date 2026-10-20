#!/usr/bin/env bash
## one crawl cycle on the pi: update code, crawl, push the snapshot to the "snapshot" branch
set -euo pipefail

repo="$HOME/internship-finder"
out="$HOME/internship-out"
data="$HOME/internship-data"
envFile="$HOME/.config/internship-finder/env"

# ntfy topic lives here, never in the repo
if [ -f "$envFile" ]; then set -a; . "$envFile"; set +a; fi

# pick up config edits made on github
git -C "$repo" pull -q --ff-only origin main || echo "git pull failed, running the code already here"

cd "$repo"
python3 -m finder --config config.yml --data "$data" --out "$out" "$@"

# push as a single fresh commit so the branch never grows
cd "$out"
rm -rf .git
git init -q
git checkout -q -b snapshot
git add -A
git -c user.name="internships-pi" -c user.email="internships-pi@users.noreply.github.com" commit -q -m "snapshot $(date -u +%FT%TZ)"
if git push -q -f git@github-internships:db165/internship-finder.git snapshot; then
  echo "pushed snapshot"
else
  echo "snapshot push failed (check the deploy key has write access)"
fi
