# Changelog — camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** für beide Seiten. Die aktuell gültige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier übereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu — sonst gilt die Version als nicht veröffentlicht.

Check „bin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

---

## 0.6.0 — 15.06.2026

- `camperfuchs-verfuegbarkeits-flow`: **NEIN-Pfad bietet jetzt optional Alternativ-Zeitraum +
  Alternativ-Fahrzeug an.** Router 11 in 6030776 hat DREI Routen — neue Modul-20-Formular-Seite
  bei `aktion=nein` (zwei optionale Freitextfelder → `alt_zeitraum`/`alt_fahrzeug` per
  GET-Formular zurück an den Hook), Modul 12 (Button-Seite) auf `aktion≠nein` verengt.
  Mieter-Entwurf (M10) baut die Alternative über zwei `if()`-Fragmente ein (leerer String =
  falsy → kein hängender Satz), bleibt Entwurf; Björn-Info (M5) zeigt die Alternative. Variante B
  (Vermieter wählt eigene Fahrzeuge) bewusst verworfen — `/api/V1/articles` kennt keinen
  Vermieter, bräuchte Backend-Endpoint.
- Gelernt + dokumentiert: der Make-**Hook** ist aus der Sandbox per `curl` testbar (Test-Rezept
  headless ohne Chrome); `scenarios_run`-`data` mappt NICHT auf Webhook-Felder; riesige
  Mapper-Strings (M10-Signatur) nie von Hand neu tippen → Python-Edit auf Rohtext + Token-Reread.

## 0.5.0 — 08.06.2026

- Neuer Skill `camperfuchs-verfuegbarkeits-flow`: Betrieb/Änderung/Troubleshooting des
  Vermieter-Verfügbarkeits-Flows (Make 5482694 + 6030776) — System-Landkarte (alle IDs),
  zweistufiger Scanner-Schutz, Antwort-Tracking (Datastore 131528), Mieter-Entwurf bei NEIN,
  Test-Rezepte und Gotchas.
- Neu darin: **Fahrzeug-Link + Telefon als Info-Buttons** in der Verfügbarkeits-Mail (M2).
  Fahrzeug-URL wird OHNE Regex-Änderung im Mapper aus `{{7.fahrzeug}}` (Format „Name [URL]")
  gezogen (`split/first/trim` + `if/contains/replace/last`, Fallback Homepage) → kein
  Parser-Risiko. Plus Schema-Falle dokumentiert: `validate_blueprint_schema` lehnt top-level
  `scheduling`/`interface` ab → vor validate/update strippen (Blueprint = name/flow/metadata).

## 0.4.0 — 07.06.2026

- Neuer Skill `camperfuchs-agent-readiness`: prüft die KI-/Agenten-Auffindbarkeit von
  camperfuchs.de (Markdown for Agents, Link-Header→llms.txt, llms.txt) per curl und
  triagiert die Agent-Discovery-Standards (OAuth/OIDC, MCP-Server-Card, ACP, x402,
  DNS-AID, WebMCP, API-Catalog) nach ECHTEM Nutzen — statt blind isitagentready-Haken zu jagen.
- Merksatz verankert: Stubs ohne echtes Backend sind schädlich (Agent versucht→scheitert→Seite
  wirkt kaputt); isitagentready-„operation was aborted" = Checker-Timeout, kein echtes Loch.

## 0.3.0 — 07.06.2026

- Neuer Skill `camperfuchs-cache-purge`: gezielter Cloudflare-Edge-Purge für
  camperfuchs.de (Skript `scripts/cf_purge.sh` — einzelne URLs, mehrere, oder `--all`,
  automatische 30er-Blöcke). Löst das Edge-Layer-Propagationsproblem (APO `s-maxage` 1 Jahr).
- **Standing Rule** im Skill verankert: nach JEDEM selbst ausgelösten WP-API-Content-Edit
  die betroffene URL sofort purgen (nicht auf Nachfrage warten).
- Hinweis: Purge-fähig ist nur der BENUTZER-Token (liegt lokal in `.secrets`, NICHT im Plugin);
  Edge-Purge deckt nicht den SPC-Disk-Cache am Origin (separates Bahti-Thema). Alternativer
  Weg: SPC-REST `POST /wp-json/spc/v1/cache/purge`.

## 0.2.0 — 03.06.2026

- Serving-Kette korrigiert (per DO-API + curl verifiziert): Live-WP-Backend =
  139.59.155.118 (Droplet `www.camperfuchs.de-wordpress`, ID 34020513) hinter
  LB 157.245.21.250 → K8s. `209.38.194.145` = `wp.` (NICHT live). Auch im
  wp-502-Runbook korrigiert.
- Neu im Projektkontext: E-Mail-Infrastruktur (Mailgun rentanda.com, Spam-Thema
  Kai/Mailtrack), Automatisierung (Make.com, Team 345711), Preis-Positionierung.

## 0.1.0 — 03.06.2026

- Erste Version: Skill `camperfuchs-projekt` (Architektur, Hosting, Repo, Caching,
  SEO/Schema, Performance, Subdomains, Design-Tokens, Konventionen) + Skill
  `wp-502-debug` (Notfall-Runbook).
