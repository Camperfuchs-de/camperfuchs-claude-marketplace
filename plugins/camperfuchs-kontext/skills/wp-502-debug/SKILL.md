---
name: wp-502-debug
description: Systematische Notfall-Diagnose wenn WordPress wp-admin HTTP 502 wirft (besonders Camperfuchs-Stack auf DigitalOcean mit Cloudflare). Trigger immer wenn Björn "wp-admin geht nicht", "502", "Bad Gateway", "site ist off", "WordPress down", "admin crasht", "Login geht nicht", "Backend hängt" oder ähnliche Symptome im Camperfuchs/Rentanda-Kontext erwähnt. Auch bei "PHP Fatal", "Memory exhausted", "Apache crash", "weiße Seite im Admin". Lieber zu früh triggern als zu spät — Diagnose-Reihenfolge spart Stunden.
metadata:
  type: skill
  scope: camperfuchs-rentanda
---

# WP-502-Notfall-Diagnose

WordPress wp-admin gibt 502 Bad Gateway — Frontend läuft (CF-Cache), aber Backend crasht. Klassisches Pattern: **unauthenticated Requests gehen, eingeloggte Sessions sterben**. Ursache fast immer eine von vier Sorten: PHP-OOM, Plugin-Crash, Cloudflare-Block, oder Apache-Worker-Hang.

Diese Reihenfolge spart Zeit weil sie schnelle Eliminierung vor langsame Tools setzt.

## Schritt 0: Symptom genau einordnen (30 Sek)

Bevor du irgendwas anfasst, **bestätige das Pattern**. Frage Björn (oder selbst checken):

- Geht die Frontend-Seite? (z.B. `www.camperfuchs.de` ohne Login)
- Geht wp-login.php (Login-Form vor dem Login)?
- Kommt der 502 erst **NACH** Login oder schon davor?

**Wenn nur authenticated 502** → klassisch Memory/Plugin/Cookie. Weiter zu Schritt 1.
**Wenn auch unauthenticated 502** → Origin komplett down, weiter zu Schritt 4 (Web Console + Apache-Check).
**Wenn nur einzelne Admin-Pages 502** → spezifisches Plugin oder Cron, weiter zu Schritt 5.

## Schritt 1: Von außen den Status prüfen (1 Min)

Aus der Cowork-Sandbox läuft:

```bash
# Frontend (sollte 200 via CF-Cache liefern)
curl -s -o /dev/null -w "Frontend: HTTP %{http_code} | %{time_total}s\n" \
  -A "Mozilla/5.0" "https://www.camperfuchs.de/"

# wp-admin unauthenticated — sollte 302 zu Login geben
for i in 1 2 3; do
  curl -s -o /dev/null -w "wp-admin Try $i: HTTP %{http_code} | %{time_total}s\n" \
    -A "Mozilla/5.0" --max-time 30 \
    "https://www.camperfuchs.de/wp-admin/admin.php?_t=$(date +%s%N)"
done

# wp-login POST mit Dummy-Credentials — sollte 200 oder 401 geben
curl -s -o /dev/null -w "wp-login POST: HTTP %{http_code} | %{time_total}s\n" \
  -A "Mozilla/5.0" --max-time 30 \
  -X POST "https://www.camperfuchs.de/wp-login.php" -d "log=test&pwd=test"
```

**Interpretation:**
- Alle 302/200/401, kein 5xx → Server ist OK für unauthenticated. Problem liegt im Login-Trigger (Memory/Plugin).
- 502/504 schon hier → Origin tot. Power Cycle nötig oder Apache-Crash.
- 502 nur via CF aber direkt am Origin nicht → CF-Konfig (selten).

## Schritt 2: Richtige Droplet identifizieren (KRITISCH)

**Größter Zeitverlust-Risiko:** Es gibt mehrere Camperfuchs-Droplets in DigitalOcean. Auf die falsche einloggen und debuggen kostet 20 Minuten.

**KORREKTUR 03.06.2026 (DO-API + curl verifiziert):** Live-www laeuft ueber CF -> DO-LB 157.245.21.250 -> K8s-Ingress -> WP-Backend 139.59.155.118 (Droplet `www.camperfuchs.de-wordpress`, ID 34020513). **209.38.194.145 ist NICHT live** (= `wp.camperfuchs.de`). Droplet-Tabelle:

| Droplet-Name | ID | IP | Hostet |
|---|---|---|---|
| `camperfuchs.de` | 402882700 | 209.38.194.145 | `wp.camperfuchs.de` (verworfen, NICHT live; liefert nur 301) |
| `new-wordpress-camperfuchs` | 528117386 | 167.172.160.66 | Bahti's Relaunch new.camperfuchs.de (8GB, Ubuntu 24.04) |
| `www.camperfuchs.de-wordpress` | 34020513 | 139.59.155.118 | **Echter Live-WP-Backend** (hinter K8s-Ingress hinter LB 157.245.21.250) |
| `camperfuchs-default-pool-*` | - | - | Kubernetes für Next.js-Inventar-App |

**Verifizieren via DNS-Resolution + Reverse-Check:**

```bash
# Welche IP zeigt die Domain?
dig +short @1.1.1.1 www.camperfuchs.de  # → CF-IPs (104.26.x / 172.67.x), Origin verdeckt
dig +short @1.1.1.1 new.camperfuchs.de  # → Origin direkt

# Wenn DO-Token verfügbar: alle Droplets mit Public-IPs auflisten
curl -s -H "Authorization: Bearer $DO_TOKEN" \
  "https://api.digitalocean.com/v2/droplets" | \
  python3 -c "import json,sys; [print(f\"{d['name']:<40} id={d['id']:<12} ip={d['networks']['v4'][0]['ip_address']}\") for d in json.load(sys.stdin)['droplets']]"
```

**Origin-IP über CF-Bypass-Test bestätigen** (wichtig wenn du den richtigen Server suchst):

```bash
# Test ob bestimmte IP wirklich Live www serviert
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  --resolve "www.camperfuchs.de:443:$ORIGIN_IP" \
  -A "Mozilla/5.0" --max-time 15 -k \
  "https://www.camperfuchs.de/"
```

**Verify per SSH-Login:** `apache2ctl -S | head` zeigt die konfigurierten VirtualHosts. Wenn dort `new.camperfuchs.de` statt `www.camperfuchs.de` steht → falsche Droplet!

## Schritt 3: Web Console öffnen

Über Cowork's Chrome-Browser:

1. Navigate: `https://cloud.digitalocean.com/droplets/<DROPLET_ID>`
2. Klick **"Web Console"** (oben rechts) — öffnet Popup-Fenster (kann der Cowork-Browser nicht direkt steuern)
3. **Login** muss Björn manuell machen (Root-PW eingeben — nicht von Claude automatisiert wegen Auth-Regel)

**Wenn Root-PW fehlt:**
- Settings Tab → "Reset Root Password" → PW kommt per Mail an `b.dunker@camperfuchs.de`
- Nachteil: Bestehende SSH-Sessions können sich nicht mehr per altem PW reauthentifizieren

**Wenn Web Console hängt/Popup blockiert:** Browser-Popup-Blocker prüfen, oder direkt URL `https://cloud.digitalocean.com/droplets/<ID>/terminal/ui` öffnen.

## Schritt 4: Standard-Diagnose-Block (im Web Console)

Sobald Root-Prompt da ist, **immer zuerst Hostname-Verify** damit du nicht auf falscher Droplet bist:

```bash
echo "=== HOSTNAME + VHOST ==="
hostname
apache2ctl -S 2>&1 | grep -E "^\*:" | head

echo ""
echo "=== Webserver-Stack identifizieren ==="
ps -eo comm | grep -Ei 'apache|nginx|php-fpm|lsws' | sort | uniq -c

echo ""
echo "=== Server-Health ==="
free -m | head -2
uptime
df -h / | tail -1

echo ""
echo "=== Letzte 50 Apache-Errors ==="
tail -50 /var/log/apache2/error.log 2>/dev/null | grep -E "php:error|Fatal|signal|Segmentation|exhausted" | tail -20

echo ""
echo "=== Aktive WP-Plugins ==="
cd /var/www/html
which wp >/dev/null && wp plugin list --status=active --allow-root 2>&1 | head -40 || ls -la wp-content/plugins/ | head
```

**Lesart:**

- `apache2` only, kein `php-fpm` → **mod_php Stack** (memory_limit in `/etc/php/X.Y/apache2/php.ini`)
- `php-fpm` und `nginx`/`apache` → **FPM Stack** (memory_limit in `/etc/php/X.Y/fpm/php.ini`)
- `lshttpd`/`lsphp` → **LiteSpeed** (memory in `/usr/local/lsws/lsphp*/etc/php/X.Y/litespeed/php.ini`)

Erstes Indiz von OOM: `[php:error] PHP Fatal error: Allowed memory size of N bytes exhausted` im Apache-Log. Klassisch 128MB Default reicht für moderne WP-Admins mit WooCommerce/Facebook-Plugin nicht.

## Schritt 5: PHP-Memory hochziehen (häufigster Fix)

Drei Stellen müssen stimmig sein:

```bash
# A) WP-Config: WP_MEMORY_LIMIT
WPCONFIG=/var/www/html/wp-config.php
LINE=$(grep -n "stop editing\|Schluss mit dem Bearbeiten\|That's all" "$WPCONFIG" | head -1 | cut -d: -f1)
if [ -n "$LINE" ]; then
  sed -i "${LINE}i define( 'WP_MEMORY_LIMIT', '512M' );\ndefine( 'WP_MAX_MEMORY_LIMIT', '512M' );" "$WPCONFIG"
else
  printf "\ndefine( 'WP_MEMORY_LIMIT', '512M' );\ndefine( 'WP_MAX_MEMORY_LIMIT', '512M' );\n" >> "$WPCONFIG"
fi

# B) WP_DEBUG_LOG aktivieren (sehen wir beim nächsten Fatal den Trigger)
sed -i "s/define( *'WP_DEBUG', *false *);/define( 'WP_DEBUG', true );\ndefine( 'WP_DEBUG_LOG', true );\ndefine( 'WP_DEBUG_DISPLAY', false );/" "$WPCONFIG"

# C) Apache-PHP memory_limit (der bestimmt am Ende — WP-Setting nur ein Limit DRINNEN)
APACHEPHP=$(ls /etc/php/*/apache2/php.ini 2>/dev/null | head -1)
echo "Apache-PHP-INI: $APACHEPHP"
grep "^memory_limit" "$APACHEPHP"
sed -i 's/^memory_limit = .*/memory_limit = 512M/' "$APACHEPHP"

# D) Apache restart damit neuer Memory greift (reload reicht NICHT für ini-Änderungen)
systemctl restart apache2 && echo "✅ Apache restarted"

# Verify
echo "=== Verify ==="
grep -E "WP_MEMORY|WP_DEBUG" "$WPCONFIG"
grep "^memory_limit" "$APACHEPHP"
```

**Wichtig:** Nach `systemctl restart apache2` (nicht reload!) ist neuer memory_limit aktiv. `reload` startet nicht die PHP-Sapi neu.

## Schritt 6: Live-Reproduce mit Tail (wenn Memory nicht reicht)

Wenn 502 trotz Memory-Fix bleibt: parallel Tail laufen lassen + im Browser Login auslösen.

```bash
# Im Web Console:
tail -f /var/log/apache2/error.log /var/www/html/wp-content/debug.log
```

**Im Browser (Inkognito):**
1. Alle Cookies für die Domain löschen (DevTools → Application → Clear site data)
2. `https://www.camperfuchs.de/wp-login.php` → Login
3. Sobald 502 → 5 Sek warten → Strg+C im Terminal

**Interpretation:**

| Was im Tail | Was es heißt | Nächster Schritt |
|---|---|---|
| `PHP Fatal error: Allowed memory size` | OOM trotz höherem Limit | Limit nochmal verdoppeln + verdächtiges Plugin temporär weg |
| `child pid X exit signal Segmentation fault (11)` | C-Extension crashed (oft GD, ImageMagick, opcache) | OPcache leeren, php-Extensions checken |
| `script timed out` / `Maximum execution time` | Langer DB-Query oder externer API-Call | `max_execution_time` hoch + slow query suchen |
| GAR NICHTS Neues | Origin sah die Anfrage nie | CF-Side prüfen (Schritt 7) |
| Plugin-spezifischer Trace | Defekter Plugin-Code | Plugin via mv wegschieben (s.u.) |

## Schritt 7: Plugin im Notfall hart deaktivieren

Wenn ein Plugin crasht und du nicht ins Admin reinkommst:

```bash
# Plugin-Ordner suchen + wegschieben (WP deaktiviert automatisch)
WPROOT=/var/www/html
PLUGIN="problem-plugin-name"
if [ -d "$WPROOT/wp-content/plugins/$PLUGIN" ]; then
  mv "$WPROOT/wp-content/plugins/$PLUGIN" "/tmp/$PLUGIN-disabled-$(date +%s)"
  echo "Plugin verschoben — beim nächsten Request deaktiviert WP es automatisch"
fi
```

Plugin-Settings bleiben in der DB. Alternativ via WP-CLI:

```bash
cd /var/www/html
wp plugin deactivate <plugin-slug> --allow-root
```

## Schritt 8: Cloudflare-Side ausschließen (wenn Origin clean)

Wenn Origin garantiert OK ist aber 502 trotzdem kommt, ist's CF. **Camperfuchs Account-IDs:**

- `1f19594872b7aa8df85c24f19a34e621` = b.dunker@-Account (hostet camperfuchs.de + .com + bluetrailer + campercare)
- `1cc531159e1e37083ee8ea1003f95a0e` = "Domains"-Account (rentanda, campander, campercare.net etc.)

Zone-ID für camperfuchs.de: `835b24e58f5c7a050c30286992c6be11`

**API-Check (Token muss Zone Read + Account Analytics Read haben):**

```bash
export CF_TOKEN="cfat_..."
export ZONE="835b24e58f5c7a050c30286992c6be11"

# WAF Managed Rules — was ist aktiv?
curl -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE/rulesets/phases/http_request_firewall_managed/entrypoint" | \
  python3 -m json.tool | grep -E "description|enabled"

# Custom Rules
curl -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE/rulesets/phases/http_request_firewall_custom/entrypoint"

# Cache Rules (manchmal cache-rule = bypass falsch → langer Origin-Hit)
curl -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE/rulesets/phases/http_request_cache_settings/entrypoint"

# Configuration Rules
curl -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE/rulesets/phases/http_config_settings/entrypoint"

# Workers Routes
curl -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE/workers/routes"

# Recent Firewall-Events (braucht Account Analytics Read scope)
SINCE=$(date -u -d "2 hours ago" '+%Y-%m-%dT%H:%M:%SZ')
QUERY='{"query":"{ viewer { zones(filter: {zoneTag: \"'$ZONE'\"}) { firewallEventsAdaptive(filter: {datetime_geq: \"'$SINCE'\"}, limit: 20, orderBy: [datetime_DESC]) { datetime action source ruleId clientRequestPath clientIP } } } }"}'
curl -s -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" \
  -d "$QUERY" "https://api.cloudflare.com/client/v4/graphql"
```

**Verdächtig:**
- "Exposed Credentials Check Ruleset" auf "Block" → blockt Login mit bekannten Leak-Passwörtern
- Cache Rule mit `cache.bypass` falsch konfiguriert → Admin-Pages werden gecached
- Worker mit Bug → eigener Worker fängt Request ab

**Schneller Test ohne Override:** WAF temporär in "Log only" Mode setzen. Wenn dann geht → WAF-Schuld. Rebuild mit Skip-Rule für `/wp-admin/*` und `/wp-login.php`.

## Schritt 9: Recovery-Eskalation

Wenn alle Stricke reißen, in dieser Reihenfolge:

1. **DigitalOcean "Restart" über Dashboard** (Actions → Restart) — Hard Reset, ~30 Sek Downtime, kann Worker-Locks lösen
2. **Akeeba Backup Restore** über kickstart.php (Bahti hat täglich Backups) — letzte Stunden Settings weg, aber Site läuft
3. **Bahti SOS-Mail/WhatsApp:** "Site down, brauche SSH-Restart von PHP-Workers oder Plugin-Disable via mv"

## Camperfuchs-spezifische Gotchas

- **Apache+mod_php-Stack** (nicht FPM!) — `systemctl restart apache2` ist der Befehl, kein "restart php-fpm"
- **Code Snippets Plugin** ist auf Live aktiv (Snippets 19=llms.txt, 22=JWKS/security.txt) — wenn ein Snippet bricht, kann Admin crashen
- **WP 6.4.1 + PHP 8.0** sind alt (Sprint-Backlog: Update — heute aber nicht Notfall)
- **APO + Super Page Cache** parallel aktiv (memory not problem, beide ergänzen sich)
- **Live-WP-Backend = 139.59.155.118** (Droplet ID 34020513, via K8s-Ingress hinter LB 157.245.21.250); 209.38.194.145 = `wp.` (NICHT live), **167.172.160.66** ist Bahti's Relaunch — nicht verwechseln!
- **Rank Math PRO** ist einziger SEO-Plugin (AIOSEO deaktiviert seit 25.05.2026)

## Schritte die NICHT helfen

Spar dir diese Zeit-Verbrauche:

- **Cache-Purge auf Cloudflare** wenn 502 von Origin kommt — bringt nichts
- **Browser-Cache leeren** ohne Inkognito — Cookies bleiben
- **Hard-Reset ohne Diagnose** wenn Memory/Plugin der Trigger ist — kommt nach Neustart sofort zurück
- **PHP-Version updaten als Notfall-Fix** — Nicht das Problem im Akutfall; gut für Sprint

## Schnell-Übersicht der häufigsten Crash-Trigger

| Symptom | Wahrscheinlichste Ursache | Schneller Fix |
|---|---|---|
| 502 nur authenticated | OOM bei Plugin-Init | WP_MEMORY_LIMIT + Apache memory_limit auf 512M |
| 502 alle Pages | Apache crashed / Worker erschöpft | `systemctl restart apache2` |
| 502 nur einzelne Admin-Page | Plugin-spezifisch | Plugin via `mv` deaktivieren |
| 502 nach CF-Änderung | WAF/Worker/Cache-Rule | CF in "Log only" testen |
| 502 zufällig schwankend | DB-Lock / langer Query | `mysqladmin processlist`, Slow-Query-Log |

## Dokumentation in Memory

Nach jeder Session: relevante neue Erkenntnisse in `[[project-camperfuchs-architecture]]` und `[[reference-camperfuchs-hosting]]` aktualisieren. Speziell wenn sich Droplet-IDs, IPs oder Hosting-Setup ändern.
