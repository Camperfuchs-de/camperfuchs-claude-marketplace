---
name: camperfuchs-kalender-sperre
description: >-
  Betrieb, Änderung und Diagnose der Camperfuchs Kalender-Sperr-Automatik — sagt ein Vermieter
  auf eine Mietanfrage NEIN, kann er den Zeitraum auf der Danke-Seite per Klick selbst im
  Kalender sperren (Make 6578305 → key-gated /api/automation/block auf srv2). IMMER nutzen,
  wenn daran gearbeitet wird — explizit ("Kalender-Sperre", "Zeitraum sperren", "Szenario
  6578305", "/api/automation/block", "unblock", "automation_apikey", "Block-Button auf der
  NEIN-Seite", "Sperre wurde nicht gesetzt", "falsches Fahrzeug gesperrt") wie implizit
  ("Vermieter pflegt seinen Kalender nicht", "gleiches Fahrzeug bekommt immer wieder
  Anfragen", "Fahrzeug ist trotz Sperre noch in der Suche", "Fehlklick rückgängig machen").
  Direkt buchbare Fahrzeuge sperrt cf-nein-sperre.php seit 11.09.2026 automatisch.
  Enthält System-Landkarte, Auth-Modell, Test-Rezept und die teuer gelernten Fallen.
  NICHT für den JA/NEIN-Grundflow (→ camperfuchs-verfuegbarkeits-flow) oder die
  Alternativen-Anfrage (→ camperfuchs-nein-alternativen-anfragen).
---

# Camperfuchs Kalender-Sperre bei NEIN

> ⚠️ **Seit 11.09.2026 hat die Cloud-Sandbox kein Egress mehr.** `dev.azure.com`,
> `www.camperfuchs.de`, `tafel.camperfuchs.de`, `api.eu.mailgun.net`, `api.cloudflare.com`
> und `eu1.make.com` antworten dort mit `connect_rejected` — das liest sich wie ein
> Serverfehler, ist aber die Egress-Policy. Erlaubt sind nur noch npm, pypi, github.com und
> api.anthropic.com. **Jedes curl-/SSH-/REST-Rezept unten läuft deshalb über den PC:**
> Desktop Commander, Skript in eine `.ps1` schreiben und per
> `powershell -NoProfile -ExecutionPolicy Bypass -File …` starten
> (`Invoke-RestMethod` / `Invoke-WebRequest` / das Git-ssh unter
> `C:\Program Files\Git\usr\bin\ssh.exe`).
>
> ⚠️ **Und die .ps1-Datei braucht ein BOM oder reines ASCII** — PowerShell 5.1 liest eine
> UTF-8-Datei ohne BOM als Windows-1252, dabei werden Umlaute und Sonderzeichen doppelt
> kodiert. Längere Texte mit Sonderzeichen deshalb nicht als Literal ins Skript schreiben,
> sondern in eine eigene Datei legen und mit
> `[System.IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)` einlesen. Außerdem frisst
> PowerShell `$`-Variablen in `-Command`-Einzeilern und bricht bei
> `$ErrorActionPreference='Stop'` schon an stderr-Rauschen ab.


Live seit 15.07.2026.

## Warum es das gibt

Vermieter sagen NEIN, weil das Fahrzeug belegt ist, pflegen den Kalender aber nicht nach.
Folge: dasselbe Fahrzeug bekommt weiter Anfragen für denselben Zeitraum, Kunden laufen ins
Leere, Vermieter nerven sich. Der Vermieter ist beim NEIN-Klick ohnehin im Browser — genau
dort fragen wir nach und schreiben die Sperre.

**Zwei Regeln, je nach Fahrzeug (Björns Entscheidung 11.09.2026):**

- **Anfrage-Fahrzeug → Klick.** Ein NEIN heißt nicht zwingend „belegt". Es heißt oft „Fahrzeug
  haben wir nicht mehr", „zu kurze Miete", „Übergabetag geht nicht". Automatisches Sperren
  würde buchbare Zeiträume dichtmachen = Umsatzverlust. Die Kette fragt bei solchen Fahrzeugen
  ohnehin jedes Mal den Vermieter.
- **Direkt buchbares Fahrzeug → automatisch.** Hier ist ein offener Zeitraum nach einem NEIN
  gefährlicher als eine Sperre zu viel: der Kunde bekommt „direkt buchbar" und kann bezahlen,
  obwohl das Fahrzeug weg ist. Siehe Abschnitt „Auto-Sperre" unten.

## System-Landkarte

1. **Make 6030776**, Modul 2 (`gateway:WebhookRespond`, die Danke-Seite nach `confirm=1`).
   Enthält am Ende `{{if(1.aktion = "nein"; "<div>…Button…</div>"; "")}}` → Button erscheint
   nur bei NEIN. Die Seite ist für ja/nein/rueckfrage dieselbe, daher die Bedingung.
2. **Make 6578305** „Kalender-Sperre bei NEIN", Hook `kdoadlc3iv8sweiggr30cfq7das9gqkk`,
   Parameter `?vermieter=…&betreff=…`:
   - M2 `datastore:GetRecord` DS **131528**, key `{{1.vermieter}}|{{1.betreff}}`
   - M4 `http` GET srv2 `/api/automation/articles-by-landlord?email={vermieter}&title={titel}`
     (key-gated per X-Automation-Key wie /block; parseResponse) — matcht den Titel seit
     10.08.2026 SERVERSEITIG fuzzy und liefert `match{count,id,title,tier}` + `content[]`.
     Vorher: Spring by-landlord + exakter Make-`map()`-Match, scheiterte an Schreibvarianten.
   - Router: Route 1 Filter „Fahrzeug eindeutig" (`4.data.match.count = 1`) → M6 POST block
     mit `4.data.match.id` → M9 Respond Erfolgsseite (zeigt `match.title`) → M7 Marker in
     DS 137664. Route 2 Filter „NICHT eindeutig" (`count ≠ 1`) → M10 Diagnose-Mail an Björn
     (inkl. count/tier) → M11 Respond „Wir kümmern uns".
3. **Endpoint** `src/ApiBundle/Controller/AutomationController.php` auf srv2
   (`/home/gaz/rent`), Routen `/api/automation/block`, `/api/automation/unblock` und
   `/api/automation/articles-by-landlord` (GET email+title, Fuzzy-Match: normalisiert auf
   lowercase/nur Buchstaben+Ziffern, Tiers exact → contains beidseitig (min. 6 Zeichen) →
   Ziel am letzten " in " gekappt (Orts-Suffix); matcht gegen short_name UND articles.title).
   Repo: Azure-Projekt „Old Camperfuchs", PR #1387 + #1801 (kompletter srv2-Live-Stand
   nachgezogen 10.08.2026 — Achtung, master hatte ~4 Jahre Drift).

## Wochentags-Ausschluss (rdo, seit 27.07.2026)

Die NEIN-Danke-Seite (6030776 M2) traegt seit 27.07. ZWEI Buttons (der Kalender-Sperre-Button
war beim Phase-4/M20-Umbau verschwunden und wurde restauriert): (1) "Zeitraum im Kalender
sperren" (wie gehabt) und (2) "Keine Anfragen mehr an diesem Wochentag" → gleicher Hook mit
`&rdo=1`. In 6578305 haengen dafuer 2 zusaetzliche Router-Routen (M20/21 Erfolg, M30/31
Fallback-Mail an Bjoern); die beiden Alt-Routen haben einen `1.rdo notexist`-Guard; auch M20/M30 prüfen seit 10.08. `4.data.match.count`. Der Tag ist
der ABHOL-Wochentag der Anfrage (`upper(formatDate(parseDate(...); "dddd"))`), gesetzt wird er
per POST `/api/automation/request-days-off` (AutomationController, key-gated wie /block, Station
via Article, idempotent add/remove) in `stations.request_days_off` (CSV aus DayOfWeek-Namen;
Enforcement im neuen Backend BookingService, Pflege-UI = cfRDO-Haekchen im Oeffnungszeiten-Tab).

## Endpoint

```
POST https://www.camperfuchs.de/api/automation/block
Header: X-Automation-Key: <key aus .secrets/legacy-automation-apikey.txt>
Body:   {"article":"JO53ER3L","from":"2026-08-01","to":"2026-08-15","reason":"…"}
→ {"status":"ok","created":true,"booking":533284,"number":"KXA87M",…}
→ {"status":"ok","created":false,"reason":"already_blocked",…}   (idempotent)

POST /api/automation/unblock   (gleicher Body ohne reason)
→ {"status":"ok","removed":1,"numbers":["KXA87M"]}
```

Sperre = Buchung mit `type = 6` (`Booking::TYPE_NOTAVAILABLE`), `scope = camperfuchs`,
Station aus dem Article. `unblock` löscht **nur exakt passende** Sperren
(article + type=6 + dateFrom + dateTo) — nie unscharf, sonst trifft es echte Buchungen.

## Auth-Modell (und warum so)

Key im Header `X-Automation-Key` gegen Parameter `automation_apikey` (`hash_equals`).
**Kein JWT, kein technischer User.** Grund: `domainAdmin` greift für Camperfuchs nicht,
weil `stations.domain` bei 3.553 Stationen NULL ist (kein `'cf'`). Ein technischer User
hätte also `ROLE_ADMIN` gebraucht → Admin-Zugangsdaten dauerhaft in Make. Wollten wir nicht.

Echter Key nur in `parameters.yml` (gitignored) + `.secrets`. `parameters.yml.dist` hat
den Parameter als Platzhalter `~`.

## Fallen (teuer gelernt)

- **Titel-Match läuft SERVERSEITIG** (seit 10.08.2026): Matching-Probleme am srv2-Endpoint
  `/articles-by-landlord` fixen, NICHT in Make-Formeln — `map()` matcht nur exakt,
  Normalisierung ist in Make-Formeln nicht machbar. Der Endpoint liefert immer ALLE
  Fahrzeuge des Vermieters (die alte `&size=500`-Falle des Spring-by-landlord entfällt).
- **DS-Feld `fahrzeug` trägt mal den SHORTNAME, mal den langen `articles.title`**
  (Fall womo-winkler 10.08.: "Chausson 648 First Line in Großenseebach" = SEO-Titel, der
  VM-Titel war "Chausson 648 FirstLine mit Queensbett" → 0 Treffer beim Exakt-Match).
  Der Server-Match deckt beide Formen, weil er gegen short_name UND title prüft.
- **Fahrzeug-Titel sauber schneiden:** DS-Feld `fahrzeug` ist roh, also
  `WEINSBERG CaraCore 650 MF [https://email.mg…]`. Nutze
  `trim(first(split(2.fahrzeug; " [https")))` — **KEIN Regex** mit `[^\]]`, das bricht in
  Make-Formeln und zerlegt außerdem Namen wie `… [PEPPER]`.
- **Nur bei genau 1 Treffer sperren.** `4.data.match.count` muss `= 1` sein, sonst
  Fallback-Mail (mit count/tier als Diagnose). Verhindert, dass das falsche Fahrzeug
  dichtgemacht wird — der Fuzzy-Match weicht die Sicherung bewusst NICHT auf.
- **Fallback-Routen brauchen einen eigenen Filter.** Eine Route ohne Filter läuft IMMER mit;
  ihre Antwortseite überholt dann die Erfolgsseite.
- **`builtin:Ignore` als onerror beendet die Route.** Ein `AddRecord` mit `overwrite:false`
  auf einen existierenden Key wirft → Ignore → alles danach (auch der `WebhookRespond`)
  entfällt → der Klicker sieht nur „Accepted". Erst antworten, dann markieren.
- **Sperre wirkt in der Suche erst nach ~20 s** (Backend-Cache). Sofort messen führt in die Irre.
- **Suchtest nur mit Datum, an dem das Fahrzeug wirklich gelistet ist.** In 2030 erscheinen
  nur 173 Fahrzeuge überhaupt — ein „ist weg" beweist dort gar nichts. Vorher/Nachher prüfen.
- **Execution-Details gibt die Make-MCP-API nicht her** (nur Status/Ops). Zum Debuggen die
  Diagnosewerte in die Fallback-Mail schreiben.

## Testen ohne echte Vermieter zu treffen

1. Test-Record in DS 131528 anlegen, key `<vermieter>|TEST …`, `fahrzeug` mit `[https…]`-Suffix,
   `zeitraum` im Format `DD-MM-YYYY bis DD-MM-YYYY`, Datum weit in der Zukunft.
2. Für den Block-Webhook: `vermieter` = echte Vermieter-Adresse (sonst liefert `by-landlord`
   nichts). Für die 6030776-Kette: `vermieter=b.dunker@camperfuchs.de`, dann landen alle
   Mails bei Björn; `mieter` leer lassen, dann entsteht kein Kunden-Entwurf.
3. Der Hook ist per curl DIREKT aus der Sandbox aufrufbar (10.08.2026 verifiziert — die alte "nur über Chrome"-Note ist überholt).
4. Danach aufräumen: DS-Records löschen (131528, 131793, 137664) und die Testsperre per
   `/api/automation/unblock` entfernen. Gegenprüfen, dass 0 Zeilen übrig sind.

## srv2-Zugang

`ssh -i ~/.sshtmp/k root@46.101.113.30` (Key `.secrets/id_srv2_cf`, nach `~/.sshtmp/` kopieren,
`/tmp` ist nicht beschreibbar). **Hostname löst in der Sandbox nicht auf, IP nutzen.**
Deploy = Datei per base64 rüberschieben, `php -l`, `php app/console cache:clear --env=prod`,
`debug:router | grep automation`. Repo separat per PR nachziehen — `/home/gaz/rent` hängt auf
detached HEAD und weicht ohnehin vom Repo ab.

## Auto-Sperre bei direkt buchbaren Fahrzeugen (seit 11.09.2026)

**Anlass #3OBEWL:** Feith (Station 3964, Chausson 640, Artikel VDP14IQA) hatte 27.09.–07.10.
schon am 17.07. per NEIN abgesagt (#S6R8RI), aber nicht geklickt. Der Kalender blieb frei, das
Fahrzeug direkt buchbar. Eine Telefon-Anfrage am 11.09. lief deshalb so: 13:30 „Gute Nachricht:
direkt buchbar" an den Kunden, 13:39 Vermieter meldet belegt, 13:44 „leider belegt, hier sind
Alternativen". Ein Online-Kunde hätte in der Zwischenzeit bezahlen können.

**Job:** `/usr/local/cf/cf-nein-sperre.php` auf srv2, Cron `/etc/cron.d/cf-nein-sperre` alle
10 Minuten, Log `/var/log/cf-nein-sperre.log`.

- Greift nur, wenn `article_locations.bookable = 1 AND visible = 1` am **Standort der Anfrage**
  (nicht `articles.bookable` — das ist nicht die Wahrheit).
- NEIN erkannt über `cf_vorgang.status = 'nein'` ODER `bookings.meta` mit
  `"vermieterDecision":"nein"` — egal über welchen Kanal (Buttons, WhatsApp, Info-Mail).
- Nur Entscheidungen ab dem Stichtag 11.09.2026 14:00 (`$STICHTAG`). Ältere NEINs haben beim
  ersten Lauf nur den Merker bekommen und werden nie angefasst.
- Gesperrt wird ab `max(Abholung, jetzt)` bis Rückgabe, über `POST /api/automation/block`.
  Ist der Zeitraum schon komplett durch type 3/5/6 belegt, nur Merker.
- Merker `cf_followup.kind = 'neinsperre'` → jede Anfrage genau einmal. Scheitert der
  Block-Aufruf, kein Merker, nächster Lauf versucht es wieder.
- Jede Sperre geht als Mail an Björn (`[Sperre auto #NR] …`) mit article/from/to für den
  Rückweg. Kappe 10 Sperren je Lauf.
- Von Hand: `php cf-nein-sperre.php` (trocken), `--live`, `--id=<bookingId>` (ohne Stichtag,
  um einen Altfall doch zu sperren). Notaus: `#` vor die Cron-Zeile.

**Offene NEIN-Zeiträume ohne Sperre finden** (für direkt buchbare Fahrzeuge): Anfragen mit
NEIN (Bedingung wie oben), `date_to > NOW()`, und je Anfrage prüfen, ob type 3/5/6 den
Zeitraum lückenlos deckt. Am 11.09.2026 übrig: nur Station 3891 (fünf Wochen, iCal aktiv) —
Björn klärt das selbst, nicht sperren.

**Warnung schon vor der Anfrage:** Die Telefon-Anfrage-Maske (`cf-telanfrage.js` v14) zeigt
in der Trefferliste „Vermieter hat hier schon abgelehnt" über
`cf-telnachpflege.php action=hinweise` (Artikel-IDs + Zeitraum → frühere NEINs, auch von
stornierten Vorgängen).

## Offen

- **Kein Protokoll für „direkt buchbar".** `article_locations_aud` (Envers) existiert, hat aber
  **0 Zeilen**: der Legacy-`ArticleController` schreibt an Envers vorbei und setzt `bookable`
  bei jedem Speichern des Fahrzeugformulars aus dem Häkchen, ohne Rollenprüfung (auch
  Vermieter selbst). Wer ein Fahrzeug wann auf direkt buchbar gestellt hat, lässt sich
  deshalb nicht mehr sagen; Apache-Logs reichen 14 Tage.
- Die WhatsApp-Freitext-Erkennung (Haiku) ist seit 15.07.2026 live → `camperfuchs-verfuegbarkeits-flow`.
- Kein „Fahrzeug ganz offline nehmen"-Button — bei „haben wir nicht mehr" (Fall ginbie/MEG)
  ist Sperren nur ein Pflaster.
