# Changelog — camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** für beide Seiten. Die aktuell gültige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier übereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu — sonst gilt die Version als nicht veröffentlicht.

Check „bin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

---

## 0.10.0 — 09.07.2026

- **Neue Skill `camperfuchs-frontend-feature-shippen`** ins Plugin aufgenommen (Idee → live:
  richtige Komponente finden, Worktree off `origin/main`, PR-/Deploy-Kette, Verifikation).
- **Schritt 5 korrigiert (teuer gelernt 09.07.):** Der Live-Beleg per JS-Bundle-Fingerprint muss
  die Chunks über `/_next/static/<buildId>/_buildManifest.js` enumerieren. Seit PR #1303
  (`perf/code-split-datepicker`) werden Datepicker/BookingCalculator lazy nachgeladen und stehen
  NICHT im initialen HTML — wer nur das HTML scannt, schließt fälschlich „Fix nicht live".
  Ergänzt: i18n-Keys sind kein Komponenten-Marker, taugliche vs. untaugliche Fingerprints,
  „Quelle schlägt Bundle", PowerShell-Fallen (`$`-Stripping, `-LiteralPath`, abgeschnittene Ausgabe).
- **Repo-Struktur repariert:** Der vollständige Quellbaum (`plugins/`, `.claude-plugin/`) liegt jetzt
  im Azure-Repo. Vorher lagen dort nur flache Dateien (Browser-Upload konnte keine Unterordner) —
  dadurch waren die Versionen **0.7.0–0.9.0 nie veröffentlicht**; mit diesem Stand nachgezogen.
- **Pflege künftig per `git push` (SSH)** statt Browser-Upload → `quellbaum.zip`-Krücke entfällt.

## 0.9.0 — 23.06.2026

- `camperfuchs-verfuegbarkeits-flow`: **Rückfrage hat jetzt ein Freitext-Formular** (Modul 30, live 23.06.). Klickt der Vermieter „Rückfrage", kommt statt der reinen Bestätigungsseite eine Formularseite (CF-Palette) mit Textfeld „Deine Frage oder Anmerkung" → neuer Webhook-Param `frage`; Modul 7 (Björn-Info-Mail) zeigt den Text im Beige-Block. Router 11 jetzt VIER Routen (Modul 12 nur noch JA via Zusatz-Filter `aktion notequal rueckfrage`; Modul 30 = `aktion equal rueckfrage`). JA/NEIN unverändert. Doku: neue Sektion „Rückfrage-Formular: Modul 30", Params- und Aufgaben-Liste ergänzt.

## 0.8.0 — 16.06.2026

- `camperfuchs-projekt`: Stand-Updates seit 03.06. nachgezogen — Origin-TLS jetzt DNS-01/Cloudflare-renewt + CF-SSL "Full (strict)" (14.06.); Backend `max-http-header-size` 64KB gegen `/api/V1/articles` HTTP-400 "Suche nicht geladen" (#816, 16.06.); Consent vereinheitlicht (11.06.) + funktionierender SPC-Cache-Purge per REST `POST /wp-json/spc/v1/cache/purge`; Cache Reserve als 3. Ebene; prod-Gate min=1 (Björn allein freigabefähig); new.camperfuchs.de = neue Homepage (WP/Kadence); /de-Routing-Backlog #533-545 live + Sitemap-lowercase-Restproblem; lokale Dev-Umgebung F:\dev\camperfuchs.

## 0.7.0 — 15.06.2026

- `camperfuchs-verfuegbarkeits-flow`: NEIN-**Modul 20 ist jetzt ein Fahrzeug-Picker** (Variante B
  LIVE) — lädt die freien Fahrzeuge des Vermieters per `GET /api/V1/articles/by-landlord?email=`
  als antippbare Radio-Liste (inkl. Kennzeichen hinter dem Namen). Die frühere Notiz „Variante B
  nicht möglich / nur Freitext" wurde entfernt.
- Neues **Backend-Muster** dokumentiert: ein vermieter-eigenes Zusatzfeld NUR in `by-landlord`
  ausliefern — Feld in `ArticleOverviewVM` mit field-level `@JsonInclude(NON_NULL)`, NICHT in
  `from()` setzen, nur in `findArticlesByLandlordEmail` anreichern (`enrichWithLicensePlate`) →
  öffentliche `/api/V1/articles`-Suche bleibt ohne das Feld. Inkl. Kennzeichen-Beispiel (PR #788),
  Spaltennamen-Falle (`licensePlateNumber`→`number_plate`, `deactivated`→`deleted`) und
  Datenschutz-Hinweis (by-landlord ist öffentlich/ohne Login → Feld per E-Mail abfragbar).

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
  die betroffene URL sofort