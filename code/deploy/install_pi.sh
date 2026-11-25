#!/usr/bin/env bash
# SI Console Pi installer. Run on the Pi, from anywhere, as your normal
# user (not root). It uses sudo only for apt and systemd.
#   bash code/deploy/install_pi.sh            install, check, do not start
#   bash code/deploy/install_pi.sh --enable   also enable and start services
# Steps: system packages, venv (with system site packages, so gpiozero
# can use the Pi 5's python3-lgpio), Python deps, vault folders, .env
# check (exists, LF line endings, chmod 600), clock check, systemd units
# rendered for this user and path, then the free smoke check. It never
# prints a key and never sends a paid API call; run the live check
# yourself: .venv/bin/python -m si_console.smoke --live
set -euo pipefail

ENABLE=0
[[ "${1:-}" == "--enable" ]] && ENABLE=1

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="$(id -un)"
say() { printf '\n== %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$RUN_USER" != "root" ]] || die "run as your normal user, not root (sudo is used where needed)"
[[ -d "$CODE_DIR/si_console" ]] || die "cannot find si_console/ under $CODE_DIR"

say "System packages"
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip python3-lgpio git-lfs >/dev/null
git -C "$CODE_DIR/.." lfs install --local >/dev/null 2>&1 || true

say "Python venv in $CODE_DIR/.venv"
if [[ ! -x "$CODE_DIR/.venv/bin/python" ]]; then
  python3 -m venv --system-site-packages "$CODE_DIR/.venv"
fi
"$CODE_DIR/.venv/bin/pip" install -q --upgrade pip
"$CODE_DIR/.venv/bin/pip" install -q -r "$CODE_DIR/requirements.txt"
"$CODE_DIR/.venv/bin/python" -c "import lgpio" 2>/dev/null \
  || echo "WARN: lgpio not importable in the venv; GPIO will not work (apt python3-lgpio)"

say "Vault folders"
VAULT="$(grep -E '^SI_VAULT_PATH=' "$CODE_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '\r' || true)"
VAULT="${VAULT:-$CODE_DIR/vault/si-console}"
mkdir -p "$VAULT"/{tasks,research,portfolio,slides,log}
echo "vault: $VAULT"

say ".env"
ENV_FILE="$CODE_DIR/.env"
[[ -f "$ENV_FILE" ]] || die "missing $ENV_FILE - copy it from your laptop: scp <laptop>/code/.env $RUN_USER@<pi>:$ENV_FILE"
# A .env made on Windows has CRLF endings and maybe a BOM. Strip both.
sed -i -e 's/\r$//' -e '1s/^\xEF\xBB\xBF//' "$ENV_FILE"
# Bring it in line with the current .env.example, keeping your values
# (backs up the old file; prints names only, never key values).
python3 "$CODE_DIR/deploy/sync_env.py" --env "$ENV_FILE" --template "$CODE_DIR/.env.example"
chmod 600 "$ENV_FILE"
echo "permissions: $(stat -c '%a %U' "$ENV_FILE")  (keys are not shown)"

say "Clock (HTTPS fails on a wrong clock; the Pi has no RTC battery by default)"
sudo timedatectl set-ntp true || true
timedatectl show -p NTPSynchronized --value 2>/dev/null | grep -q yes \
  && echo "clock synced" || echo "WARN: clock not synced yet; the smoke check will test it"

say "systemd units for user $RUN_USER, code dir $CODE_DIR"
for unit in bridge coordinator; do
  sed -e "s|@USER@|$RUN_USER|g" -e "s|@CODE_DIR@|$CODE_DIR|g" \
    "$CODE_DIR/systemd/$unit.service" | sudo tee "/etc/systemd/system/$unit.service" >/dev/null
done
sudo systemctl daemon-reload

say "Free smoke check (no paid calls)"
SMOKE_OK=1
(cd "$CODE_DIR" && .venv/bin/python -m si_console.smoke) || SMOKE_OK=0

if [[ $ENABLE == 1 ]]; then
  [[ $SMOKE_OK == 1 ]] || die "smoke check failed; fix it before enabling the services"
  say "Enabling services"
  sudo systemctl enable --now bridge.service coordinator.service
  systemctl --no-pager --lines=0 status bridge.service coordinator.service || true
else
  say "Done. Next:"
  echo "  1. one live call per model:  cd $CODE_DIR && .venv/bin/python -m si_console.smoke --live"
  echo "  2. start services:           bash $CODE_DIR/deploy/install_pi.sh --enable"
fi
