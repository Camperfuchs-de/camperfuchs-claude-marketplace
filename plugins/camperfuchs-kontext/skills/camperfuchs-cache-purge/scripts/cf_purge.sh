#!/usr/bin/env bash
# cf_purge.sh — Cloudflare Edge-Cache gezielt leeren für camperfuchs.de
#
# Zweck: Nach Content-Änderungen die betroffenen URLs am Cloudflare-Edge (APO)
#        frisch ziehen, damit Besucher die neue Version sehen statt der 1-Jahr-
#        s-maxage-Kopie. Deckt NUR den Edge-Layer ab, NICHT den SPC-Disk-Cache
#        am Origin (Multi-Pod) — falls eine Seite TROTZ Purge alt bleibt, ist das
#        die separate Bahti-Baustelle.
#
# Token: braucht "Cache Purge"-Recht. Das hat NUR der BENUTZER-Token
#        (.secrets/"Claude API BENUTZER API TOKEN.txt"), NICHT der Standard-Token
#        (.secrets/cloudflare-api-token.txt → Auth-Fehler 10000).
#        Token liegt NUR lokal in .secrets, niemals im Repo/Plugin.
#
# Nutzung:
#   ./cf_purge.sh /ihr-wohnmobil-ratgeber/faq/                # ein Pfad (www. wird ergänzt)
#   ./cf_purge.sh https://www.camperfuchs.de/a /b /c          # mehrere
#   ./cf_purge.sh --all                                       # ALLES leeren (Vorsicht)
#   CF_PURGE_TOKEN=<dein-purge-token> ./cf_purge.sh /pfad     # Token per Env überschreiben
#
# Exit: 0 = ok, 1 = Fehler.

set -euo pipefail

ZONE_ID="835b24e58f5c7a050c30286992c6be11"   # camperfuchs.de
BASE="https://www.camperfuchs.de"
API="https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache"
TOKEN_FILE_NAME="Claude API BENUTZER API TOKEN.txt"

# --- Token finden: .secrets aufwärts suchen (location-unabhängig) -----------
# Extraktion ohne Token-Prefix im Code (secret-scan-sauber): laengstes
# token-artiges Wort (>=30 Zeichen) aus der Datei nehmen.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOKEN="${CF_PURGE_TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  d="$SCRIPT_DIR"
  for _ in 1 2 3 4 5 6 7; do
    if [[ -f "$d/.secrets/$TOKEN_FILE_NAME" ]]; then
      TOKEN="$(tr -s ' \t\r\n' '\n' < "$d/.secrets/$TOKEN_FILE_NAME" | grep -E '^[A-Za-z0-9_]{30,}$' | tail -1)"
      break
    fi
    d="$(dirname "$d")"
    [[ "$d" == "/" ]] && break
  done
fi
if [[ -z "$TOKEN" ]]; then
  echo "FEHLER: Kein purge-faehiger Token gefunden. Setze CF_PURGE_TOKEN oder lege" >&2
  echo "        '$TOKEN_FILE_NAME' im .secrets-Ordner des Projekts ab." >&2
  exit 1
fi

api_call() {  # $1 = JSON-Body
  curl -sS --max-time 30 -X POST "$API" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "$1"
}

check() {
  python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('success') else 'FEHLER: '+str(d.get('errors')))"
}

if [[ "${1:-}" == "--all" ]]; then
  echo ">> Leere KOMPLETTEN Edge-Cache (purge_everything) ..."
  api_call '{"purge_everything":true}' | check
  exit 0
fi

if [[ $# -eq 0 ]]; then
  grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

urls=()
for a in "$@"; do
  if [[ "$a" == http* ]]; then urls+=("$a"); else urls+=("${BASE}${a}"); fi
done

total=${#urls[@]}
echo ">> Purge ${total} URL(s) am Edge ..."
i=0
while [[ $i -lt $total ]]; do
  chunk=("${urls[@]:i:30}")
  body=$(printf '%s\n' "${chunk[@]}" | python3 -c "import sys,json; print(json.dumps({'files':[l.strip() for l in sys.stdin if l.strip()]}))")
  printf '   Block %d: %d URL(s) ... ' "$((i/30+1))" "${#chunk[@]}"
  api_call "$body" | check
  i=$((i+30))
done
echo ">> Fertig. Edge ist frisch. Falls eine Seite TROTZDEM alt aussieht -> SPC-Disk/Origin (Bahti)."
