#!/usr/bin/env bash
## one-time raspberry pi setup for the internship finder (safe to re-run)
## run with:  curl -fsSL https://raw.githubusercontent.com/db165/internship-finder/main/pi/setup.sh | bash
## re-run with:  cd ~/internship-finder && git pull && bash pi/setup.sh
## leaves the car finder (carfinder.service/timer, carfinder_deploy key, github-carfinder alias) untouched
set -euo pipefail

# wrapped in main so bash reads the whole file before running it (curl | bash safe)
main() {

repo="$HOME/internship-finder"
key="$HOME/.ssh/internships_deploy"
envDir="$HOME/.config/internship-finder"
envFile="$envDir/env"

echo "== 1/6 checking packages"
if ! python3 -c "import requests, yaml" 2>/dev/null || ! command -v git >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq git python3 python3-requests python3-yaml > /dev/null
fi

echo "== 2/6 downloading the code"
if [ -d "$repo/.git" ]; then
  git -C "$repo" pull -q --ff-only origin main
else
  git clone -q https://github.com/db165/internship-finder.git "$repo"
fi

echo "== 3/6 ntfy topic (stored only on this pi, in $envFile)"
mkdir -p "$envDir" && chmod 700 "$envDir"
current=""
if [ -f "$envFile" ]; then current=$(sed -n 's/^NTFY_TOPIC=//p' "$envFile"); fi
if [ -n "$current" ]; then
  echo "Using the topic already saved here (delete $envFile to change it)."
else
  suggested="internships-$(head -c 8 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  echo "Pick a NEW topic name, different from your car alerts. Anyone who knows it can read it, so keep it random."
  read -r -p "Topic [$suggested]: " topic < /dev/tty || true
  topic="${topic:-$suggested}"
  printf 'NTFY_SERVER=https://ntfy.sh\nNTFY_TOPIC=%s\n' "$topic" > "$envFile"
  chmod 600 "$envFile"
  echo "Saved. Subscribe to \"$topic\" in the ntfy app."
fi

echo "== 4/6 creating a key that can push to this one repo only"
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
[ -f "$key" ] || ssh-keygen -q -t ed25519 -N "" -C "internships-pi" -f "$key"
if ! grep -q "Host github-internships" "$HOME/.ssh/config" 2>/dev/null; then
  cat >> "$HOME/.ssh/config" <<EOC

Host github-internships
  HostName github.com
  User git
  IdentityFile $key
  IdentitiesOnly yes
EOC
  chmod 600 "$HOME/.ssh/config"
fi
grep -q "^github.com " "$HOME/.ssh/known_hosts" 2>/dev/null || ssh-keyscan -q github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null

keyWorks() { local out; out=$(ssh -n -o BatchMode=yes -T git@github-internships 2>&1 < /dev/null || true); [[ "$out" == *"internship-finder"*"successfully authenticated"* ]]; }
until keyWorks; do
  echo
  echo "Add this key on GitHub: db165/internship-finder -> Settings -> Deploy keys -> Add deploy key"
  echo "Title: raspberry pi    Key: (the line below)    and CHECK 'Allow write access'"
  echo
  cat "$key.pub"
  echo
  read -r -p "Press Enter once it's saved... " < /dev/tty || true
done
echo "GitHub accepted the key."

echo "== 5/6 scheduling a run every 15 minutes (separate from the car finder)"
sudo tee /etc/systemd/system/internships.service > /dev/null <<EOU
[Unit]
Description=internship finder crawler
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=$USER
ExecStart=/bin/bash $repo/pi/run.sh
TimeoutStartSec=25min
Nice=10
MemoryMax=350M
EOU
sudo tee /etc/systemd/system/internships.timer > /dev/null <<EOU
[Unit]
Description=run the internship finder every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
EOU
sudo systemctl daemon-reload
sudo systemctl enable --now internships.timer > /dev/null

echo "== 6/6 first run (checks every board once, a few minutes on a pi 3, no alerts this time)"
sudo systemctl start internships.service || true
journalctl -u internships -n 200 --no-pager -o cat | sed -n '/^company /,$p'

set -a; . "$envFile"; set +a
curl -fsS -H "Title: Internship finder is set up" -H "Tags: white_check_mark" \
  -d "You'll get a ping here when a new matching posting appears." "${NTFY_SERVER:-https://ntfy.sh}/$NTFY_TOPIC" > /dev/null \
  && echo "Sent a test ping to your ntfy topic."

echo
echo "All set. Useful commands:"
echo "  journalctl -u internships -n 60          # last run's log"
echo "  systemctl list-timers internships        # when it runs next"
echo "  journalctl -u internships -n 200 -o cat | sed -n '/^company /,\$p'   # per-board status table from the last full check"
}

main "$@" < /dev/null
