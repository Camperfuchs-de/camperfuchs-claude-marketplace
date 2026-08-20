---
name: camperfuchs-verfuegbarkeits-flow
description: Betrieb, Änderung und Troubleshooting des Camperfuchs Vermieter-Verfügbarkeits-Flows (Make-Szenarien 5482694 + 6030776, live seit 04.06.2026) — Verfügbarkeits-Mail mit JA/NEIN/Rückfrage-Buttons, zweistufige Bestätigung gegen Scanner-Fehlklicks, automatischer Gmail-Entwurf an Mietinteressenten bei NEIN (mit Alternativ-Optionen) UND bei JA (»Gute Nachricht«-Mail mit Anzahlungs-/Zahlungsdaten), automatische Kontaktdaten-Mail an den Vermieter bei JA, WhatsApp an den Kunden bei Rückfrage, Antwort-Tracking im Datastore + Live-Dashboard. IMMER nutzen bei Fragen rund um den Flow — explizit ('Verfügbarkeits-Mail ändern', 'Vermieter-Buttons', 'Szenario 5482694/6030776', 'Mieter-Entwurf bei Nein/Ja', 'Rückfrage-WhatsApp') wie implizit ('Vermieter sagt er hat geklickt aber nichts passiert', 'Kunde hat keine Antwort bekommen', 'wer hat nicht reagiert', 'Mail-Design anpassen'). Enthält System-Landkarte (Stand 27.07.2026, alle IDs), Test-Rezepte, Stale-Base-Schutzregeln und teuer gelernte Gotchas.
---

# Camperfuchs Verfügbarkeits-Flow (Vermieter-Buttons + Tracking)

> **NEU (14.07.2026) — eigene Skill für "Alternativen anfragen":** Der Button "Freie Alternativen anfragen" in der NEIN-Info-Mail (Modul 5), die Picker-Seite mit freien Fahrzeugen + Filtern (Personen/minBeds, Bauart, Preis, Haustiere, Umkreis), der direkte Anfrage-Versand an den jeweiligen Alt-Vermieter und der Backend-Endpoint `landlord-contact` sind in einem EIGENEN Make-Szenario **6559455** (Hook `m5jc…`) + Backend. Dafür die Skill **`camperfuchs-nein-alternativen-anfragen`** nutzen. Hier (5482694/6030776) geht es um den Grund-Flow (JA/NEIN/Rückfrage, Tracking, Mieter-Entwurf, Vermieter-eigener Picker Modul 20).

> **NEU (15./16.07.2026) — Kontaktdaten-Maskierung bei Anfrage-Fahrzeugen ist LIVE:** Details im Abschnitt „Kontaktdaten-Maskierung" unten. Kurz: maskierte Anfragen kommen als office@-Mail mit Marker-Zeilen an, 5482694 hat dafür Parser M25 + Router M27 mit Route B (M26 = Mail OHNE Telefon/Anrufen/WhatsApp und OHNE mieter= in den Button-URLs), 6030776 holt die Mieter-Mail per Datastore-Fallback. ⚠️ **Seit 29.07.2026 schickt 6030776 die Kontaktdaten NICHT mehr automatisch bei JA** — M60 ist entfernt, die Freigabe ist ein eigener Klick (Szenario 6752917). Siehe Abschnitt „Übergabepunkt“.

Arbeitsweise (chirurgische Blueprint-Edits, validate vor update) steht in `camperfuchs-make` — die gilt hier immer mit. ⚠️ Korrektur 15.06.: der Make-**Hook** `hook.eu1.make.com/…` IST aus der Sandbox per `curl` erreichbar (siehe Test-Rezept), auch wenn die make.com-**App/API** es nicht ist.

## ⚠️ Wer verschickt welche Mail — die wichtigste Korrektur (Stand 20.08.2026, live verifiziert)

Falsche Annahmen an dieser Stelle haben mehrfach zu Fehldiagnosen gefuehrt. Der geprueste Stand:

| Mail | Absender | Weg |
|---|---|---|
| Anfrage-Bestaetigung an Mieter + office@ | Spring-Backend (`MailService.sendBookingRequestEmails`) | Mailgun `mg.camperfuchs.de` |
| Verfuegbarkeits-Mail an den Vermieter | **Make 5482694** | Gmail-Connection (Bjoerns Konto) |
| Interne JA/NEIN/Rueckfrage-Info an Bjoern | **Make 6030776** (M6/M5/M7) | Gmail |
| **Zusage-Mail an den Mietinteressenten (JA)** | **`/usr/local/cf/cf-decmail.php` auf srv2**, Cron alle 2 Min | Mailgun |
| **Absage-Mail mit Alternativen (NEIN)** | ebenfalls `cf-decmail.php` | Mailgun |
| Rueckfrage an den Mieter | Make 6030776 **M52** (einzige Kundenmail im Szenario) | Gmail |
| Kontaktdaten-Mail an den Vermieter | `cf-contact-release.php` auf srv2 (Make 6752917 ruft nur auf) | Mailgun |
| „Fahrzeug ist direkt buchbar" an den Mieter | `cf-directbook.php` auf srv2, Cron alle 10 Min | Mailgun |

**Make hat im JA- und im NEIN-Zweig KEIN Kundenmail-Modul mehr.** Am 20.08.2026 gegen den
Live-Blueprint geprueft: 6030776 hat **59 Module**, und **M22, M24 und M10 existieren nicht mehr** —
im ganzen Szenario gibt es **kein einziges `google-email:ActionCreateDraft`**. Der JA-Zweig ist
M6 → M21 GetRecord → M25 HTTP → M62/M63 Datastore, sonst nichts. Wer eine fehlende oder doppelte
Kundenmail sucht, schaut ZUERST in `/var/log/cf-decmail.log` auf srv2, nicht in Make.

**Restposten:** Die NEIN-Info-Mail an Bjoern (M5) verspricht im Text noch einen „Antwort-Entwurf …
liegt in den Gmail-Entwuerfen" — dahinter steckt kein Modul mehr. Text bei Gelegenheit korrigieren.

**Faustregel:** Mail ueber Mailgun = ein System hat sie geschrieben (Spring/srv2/Worker). Mail aus
Bjoerns Gmail-Konto = Make oder Bjoern selbst.

## System-Landkarte (Stand 27.07.2026)

> ⚠️ **Historischer Stand.** Die Modulzahlen und die Mail-Module dieses Kapitels sind ueberholt:
> Stand 20.08.2026 hat 6030776 **59 Module**, und **M22/M24/M10 (Mieter-Entwuerfe) gibt es nicht
> mehr** — siehe Korrektur-Kapitel oben. Alles ausserhalb der Mail-Module (Router-Aufbau, Filter,
> Datastores, Picker) gilt weiter.

**Flow:** Neue Mietanfrage (Mail von noreply@) → **5482694 „Integration Gmail"** schickt dem Vermieter die Verfügbarkeits-Mail mit 3 Antwort-Button-Links + 2 Info-Buttons + loggt `status=offen` (seit 14.07. via Router **M27**: Route A = M2 normal, Route B = M26 maskiert — siehe Maskierungs-Abschnitt) → Klick landet bei **6030776 „Vermieter Verfügbarkeit – Button-Antworten"** (Webhook `3164869`, URL `https://hook.eu1.make.com/tu2xumx8rhjynvul6l2stjxq7r5mcc55`).

**6030776 ist ZWEISTUFIG** (Scanner-Schutz, seit 04.06. ~20 Uhr; Router 11 hat seit 23.06. VIER Routen):
- ohne `confirm`-Param: bei **NEIN → Modul 20 Fahrzeug-Picker-Formular** (lädt per JS die freien Fahrzeuge des Vermieters als antippbare Radio-Liste via `by-landlord` — inkl. Kennzeichen hinter dem Namen — plus Freitext-Fallback + „Alternativer Zeitraum"); bei **Rückfrage → Modul 30 Freitext-Formular** (Textfeld „Deine Frage oder Anmerkung" → Param `frage`); bei **JA → Modul 12 Button-Seite**. Alle drei rufen dieselbe URL mit `confirm=1` + allen Params (+ ggf. `alt_zeitraum`/`alt_fahrzeug` aus M20 bzw. `frage` aus M30) auf. Filter: Modul 12 = `confirm notexist` UND `aktion text:notequal nein` UND `aktion text:notequal rueckfrage` (= nur JA + Fallback); Modul 20 = `confirm notexist` UND `aktion text:equal nein`; Modul 30 = `confirm notexist` UND `aktion text:equal rueckfrage`.
- mit `confirm=1` → Modul 2 Danke-Seite → Modul 13 UpdateRecord (Tracking) → Modul 8 DeleteRecord (24h-Reminder-Stopp, Datastore 124997) → **Router 3 mit DREI Routen** (das Szenario hat insgesamt **38 Module** (inkl. M98/M99 Phase-4 decision-Call)):
  - **NEIN** (Route zu M4): **M40 GetRecord** (DS 131528) → **M42 HTTP** `/api/V1/articles/by-landlord` → **M44 Nominatim-Geocode** → **M4** Kalender-Erinnerung an den Vermieter → **M5** Info-Mail an Björn mit Button „Freie Alternativen anfragen" — Picker-Hook `m5jcmvmvw2dkfoyv6vp9q5i3fla2k31a` mit `alt=1`, `from`/`to` (aus `40.zeitraum`), `address`/`lat`/`lon` (`44.data` bzw. 42-Fallback), `mieter={{if(1.mieter; 1.mieter; 40.mieter)}}`, `vorname`, `betreff`, `personen=40.personen` → **M10 Gmail-ENTWURF an den Mietinteressenten** (to + Filter ebenfalls mit `40.mieter`-Fallback; Betreff „Deine Wohnmobil-Anfrage bei Camperfuchs", personalisiert mit `{{1.vorname}}`, volle Signatur, conditional Alternativ-Absatz — Vorlage: `04_Setup-Anleitungen/Gmail-Signatur-Vorlage.html`). Außerdem **M20 = Vermieter-Picker** (eigene Alternative des ABSAGENDEN Vermieters, zeigt Kennzeichen) — nicht verwechseln mit dem Alt-Vermieter-Picker (Szenario 6559455 → Skill `camperfuchs-nein-alternativen-anfragen`).
  - **JA** (`aktion=ja`): **M6** Info-Mail an Björn → **M21 GetRecord** (DS 131528) → **M25 HTTP** by-landlord → **M22 Gmail-ENTWURF an den Mietinteressenten** „Gute Nachricht zu deiner Wohnmobil-Anfrage bei Camperfuchs" (dynamisch: Fahrzeugname, Zeitraum, Fahrzeug-Link, Online-Buchen-Button bzw. Anzahlungs-/Überweisungsdaten — 20 % Anzahlung, VOLLER Betrag wenn Mietbeginn ≤ 30 Tage; Vermieter in CC; to + Filter mit `21.mieter`-Fallback; onerror-Fallback **M24** = vereinfachter statischer Entwurf; seit 27.07. M24-to/Filter mit `21.mieter`-Fallback und M22-Formeln `get(map(ifempty(25.data.content; emptyarray); …))` — wirft nicht mehr, wenn das Fahrzeug nicht in by-landlord steckt) → **M62 SearchRecord** + **M63 UpdateRecord** (No-Response-Selbstheilung). ⚠️ **M60 ist seit 29.07.2026 NICHT mehr in dieser Route** — Kontaktdaten gehen erst nach der Freigabe raus (Szenario 6752917); M6 trägt dafür den Button „Kontaktdaten jetzt freigeben“.
  - **RÜCKFRAGE** (`aktion=rueckfrage`): **M7** Info-Mail an Björn — zeigt den Vermieter-Freitext im Beige-Block „Frage des Vermieters" via `{{if(1.frage; 1.frage; "(keine Angabe …)")}}` (`white-space:pre-wrap`) — → **M50–M53 WhatsApp** `sendTemplateMessage` (Template `rueckfrage_kunde::de`, Filter „Mobil + Frage vorhanden", **M51/M53** = Ignore-Fallbacks).

**Webhook-Params:** `aktion` (ja|nein|rueckfrage), `vermieter`, `betreff`, `mieter` (Mieter-E-Mail), `vorname`, `confirm`, **`alt_zeitraum`/`alt_fahrzeug`** (optional, nur aus dem NEIN-Formular Modul 20), **`frage`** (optional, nur aus dem Rückfrage-Formular Modul 30). Neue Params kommen dynamisch durch (kein `metadata.interface`-Eintrag nötig — vgl. `alt_*`/`frage`).

**Tracking:** Datastore **131528** „Verfügbarkeits-Tracking" (Struktur 444568), Key = `vermieter|betreff`. Felder: vermieter, kunde, fahrzeug, zeitraum, mieter, betreff, status (offen|ja|nein|rueckfrage), gesendet, beantwortet. 5482694 schreibt AddRecord (overwrite, onerror Ignore); 6030776 Confirm-Route UpdateRecord (Teilupdate, onerror Ignore). „offen" = nie bestätigt geklickt. (Zweiter „geklickt"-Datastore **131793**, Key `vermieter|betreff|aktion`.)

**Dashboard:** Cowork-Artefakt `verfuegbarkeits-antworten` — liest Datastore live via Make-MCP `data-store-records_list` (dataStoreId 131528). Zwei Tabs: Anfragen (KPIs + Filter-Tabelle) und Vermieter (pro Vermieter: Anfragen, JA/NEIN/Rückfrage/Offen, Antwortquote, Ø Reaktionszeit). Ändern via `update_artifact`.

**Design (von new.camperfuchs.de, Kadence-Palette):** weißer Header mit Badge-Logo `www.camperfuchs.de/wp-content/uploads/2026/06/CF_Logo_Badge_320x280.png` (Media-ID 19625), Titel-Band Braun `#89521f` weiß UPPERCASE, Datenblock Beige `#efeae6` (Kunde, Fahrzeug, Reisezeitraum, Bemerkung), darunter **2 braune Info-Buttons `#89521f`** („Fahrzeug ansehen" / „{{telefon}} anrufen", OHNE Emoji-Icons — Björn-Wunsch 08.06.), Text Anthrazit `#28383d`/`#484745`, dunkler Footer `#202020` mit weißem Logo `…/CF_Logo_Header_White.png` (ID 19626), Antwort-Buttons JA `#2e7d32` / NEIN `#c62828` / Rückfrage weiß mit Braun-Outline. Formular-Seite (Modul 20) übernimmt dieselbe Palette. Referenz-HTML: `01_Architektur-Tech/Vermieter-Verfuegbarkeitsmail_Buttons_2026-06-08_Vorschau.html`, `01_Architektur-Tech/Verfuegbarkeit-NEIN-Formular_2026-06-15_Vorschau.html`.

**Connections:** Gmail v4 `6998308` (Trigger, sendAnEmail, createADraft) · Google Restricted `7458024` (ActionSendEmail v2).

## Phase-4 decision-Call M99 (entkoppelt 27.07.2026)

**M99** postet nach jeder Bestätigung die Entscheidung ans Backend
(`POST /api/V1/bookings/{{1.nr}}/decision?aktion=…`, Header X-CF-Automation-Secret), Filter
„nr vorhanden", onerror **M98** Ignore. Seit 27.07. hängt M99 als EIGENE vierte Route unter
Router 3 — vorher (25.–27.07.) saß er in der linearen Confirm-Kette VOR Router 3, wodurch
JEDER Klick ohne `nr`-Param (Mails vor ~21.07.) und jeder Backend-Fehler (404/500 → Ignore)
die GESAMTE Nachverarbeitung still killte (kein M6/M22/M60, Ausführung trotzdem „Erfolg",
nur 5 Ops statt 13/14). **NIE zurück in die lineare Kette bauen** — Make-Filter/Ignore stoppen
dort die ganze Route, Router-Routen sind dagegen voneinander isoliert.

## Regex in 5482694 (Modul 7)

Parst aus der Anfrage-Mail: fahrzeug, zeitraum, vorname, nachname, **email** (`E-mail: (?<email>\S+)` — exakt diese Schreibweise im Mail-Template!), telefon, bemerkung. Bei neuen Feldern: Regex erweitern + `metadata.interface` ergänzen + Button-URLs (`&mieter=…&vorname=…`-Muster) + ggf. Bestätigungs-Seiten-URL in 6030776 nachziehen — alle drei Stellen, sonst kommt das Feld nicht durch.

**Wichtig — Regex NICHT für jede Kleinigkeit anfassen:** Der Parser (`continueWhenNoRes:true`) liefert bei Nicht-Match LEERE Felder → Verfügbarkeits-Mail geht mit leeren Werten raus an einen echten Partner. Wenn ein neuer Wert nur aus einem schon geparsten Feld ableitbar ist (siehe Fahrzeug-URL unten), lieber im **Mapper** extrahieren statt den Live-Regex umzuschreiben.

## Fahrzeug-Link & Telefon als Buttons (M2, seit 08.06.2026)

`{{7.fahrzeug}}` kommt im Plain-Text-Link-Format **„Name [URL]"** (z.B. `Kulba Rebell x-Line [https://email.mg.camperfuchs.de/c/…]`). camperfuchs.com-Partner-Mails haben die `[URL]`, manche Fremd-Partner-Mails NUR den Namen (ohne Bracket). URL OHNE Regex-Änderung direkt im Mapper ziehen (kein Parser-Risiko):

- **Fahrzeugname (Anzeige, ohne Roh-URL):** `{{trim(first(split(7.fahrzeug; "[")))}}`
- **Fahrzeug-URL (Button-href):** `{{if(contains(7.fahrzeug; "["); trim(replace(last(split(7.fahrzeug; "[")); "]"; "")); "https://www.camperfuchs.de")}}` — Fallback Homepage, wenn keine `[URL]` da ist.
- **Telefon-Button:** `href="tel:{{7.telefon}}"`, Beschriftung `{{7.telefon}} anrufen`.

Die Semikolons in diesen Formeln sind Argument-Trenner; die String-Literale (`"["`, `"]"`, `""`, URL) enthalten selbst KEINE Semikolons → unkritisch (vgl. Gotcha unten: keine HTML-Blöcke mit `;` in if()). Make speichert die IML 1:1 (zurückgelesen, `isinvalid:false`). Runtime-Funktionen (`split/first/last/trim/replace/contains/if`) sind Standard.

## NEIN-Alternative: Modul 20 = Fahrzeug-Picker (Variante B LIVE seit 15.06.2026)

Klickt der Vermieter NEIN, kommt **Modul 20** = Formular-Seite, die **per JS die EIGENEN freien Fahrzeuge des Vermieters lädt und als antippbare Radio-Liste zeigt** (Variante B — ist umgesetzt; die frühere Notiz „nur Freitext / B nicht möglich" ist überholt). Quelle: Backend-Endpoint `GET https://www.camperfuchs.de/api/V1/articles/by-landlord?email={{1.vermieter}}` (löst E-Mail→Station→`getFilteredArticlesByStation`; liefert NUR aktive Fahrzeuge: `deleted=0`/template=0/`visible=1`). CORS am Endpoint erlaubt den make.com-Origin → `fetch` aus der Seite geht. Auswahl setzt Hidden `alt_fahrzeug` (title) + `alt_url` (uri→Deeplink). Daneben weiter: Freitextfeld (Fallback) + `alt_zeitraum`. Leer lassen = Absage exakt wie früher. Scanner-sicher (Formular-Submit = Page-Button).

**Modul 10 Kunden-Entwurf** baut die Alternative über zwei `if()`-Fragmente ein (Make-Truthiness: leerer String = falsy → kein hängender Satz):
`{{if(1.alt_fahrzeug; " Der Vermieter hätte zum Beispiel dieses Fahrzeug frei: " + 1.alt_fahrzeug + "."; "")}}{{if(1.alt_zeitraum; " Ein möglicher Zeitraum wäre: " + 1.alt_zeitraum + "."; "")}}` + conditional Deeplink-Button aus `alt_url`. Eingebettet im Basissatz „Die gute Nachricht: …". **Bleibt Entwurf** (siehe `camperfuchs-alternativ-angebot`).

### Vermieter-eigenes Zusatzfeld im Picker zeigen (Backend-Muster, erprobt 15.06. mit Kennzeichen, PR #788)
Der Picker rendert pro Fahrzeug das, was `by-landlord` liefert. Ein zusätzliches Feld (z.B. Kennzeichen) sichtbar machen = zwei Schritte:
1. **Backend (Monorepo, selbst deploybar):** Feld der **`ArticleOverviewVM`** hinzufügen, aber **field-level `@JsonInclude(JsonInclude.Include.NON_NULL)`** und **NICHT in `from()` setzen** → die ÖFFENTLICHE `/api/V1/articles`-Suche bleibt ohne das Feld (Datenschutz). Nur `ArticleService.findArticlesByLandlordEmail` reichert nach (`articleRepository.findByIdIn(ids)` → Getter, je VM setzen, nur wenn nicht leer = `enrichWithLicensePlate`-Muster). ⚠️ **Spaltennamen-Falle:** Entity-Feld ≠ DB-Spalte — `licensePlateNumber`→`number_plate`, `deactivated`→`deleted`. Vor Native-Query/Getter `@Column(name=…)` prüfen.
2. **Make Modul 20 JS:** in der Radio-Schleife `items[i].<feld>` lesen und escaped hinter den Namen hängen: `var pl = esc(items[i].licensePlate); var lab = pl ? (t + " <span style='color:#89521f;font-weight:600'>&middot; " + pl + "</span>") : t;` (esc() = &/</> ersetzen).

⚠️ **Datenschutz:** `by-landlord` ist **öffentlich/ohne Login** → jedes dort ausgelieferte Feld ist per Vermieter-E-Mail abfragbar. Bei personenbezogenen Feldern (Kennzeichen!) vorher Björn-OK. Kennzeichen-Werte sind teils Vermieter-Freitext mit Zusatz („MO-DJ-224 (Frei)") → bewusst 1:1 angezeigt (nur der Vermieter sieht den Picker).

## Rückfrage-Formular: Modul 30 (LIVE seit 23.06.2026)

Klickt der Vermieter **Rückfrage**, kam früher nur die reine Bestätigungsseite (Modul 12) und Björn bekam eine inhaltslose Info-Mail. Jetzt: eigene Router-11-Route **Modul 30** = `gateway:WebhookRespond`-Formularseite (CF-Palette wie M20/M12) mit einem `<textarea name='frage'>` „Deine Frage oder Anmerkung" (optional). Submit (`method=get`) ruft die Hook-URL mit `confirm=1&aktion=rueckfrage&…&frage=…` → normale Confirm-Route → **Modul 7** Info-Mail an Björn mit dem Frage-Text. Scanner-sicher (Submit = Page-Button, kein Mail-Link). Filter Modul 30 = `confirm notexist` UND `aktion text:equal rueckfrage`; im Gegenzug bekam Modul 12 die Zusatz-Bedingung `aktion text:notequal rueckfrage` (sonst feuern beide). JA und NEIN unverändert. `frage` ist optional → Modul 7 zeigt bei leer „(keine Angabe …)".

## Kontaktdaten-Maskierung bei Anfrage-Fahrzeugen (LIVE seit 15.07.2026, prod-verifiziert)

Provisions-Leakage-Schutz: Bei Mietanfragen auf Fahrzeuge, die an der Station NICHT direkt buchbar sind (`article_locations.bookable != true`, `BookingType.REQUEST`), bekommt der Vermieter die Mieter-Kontaktdaten erst nach seiner JA-Bestätigung.

**Spring-Seite (Monorepo, PR #1367):** `EmailTemplateService.isContactMasked(booking)`; `MailService.sendBookingRequestEmails` überspringt die Station — die Partner-Mail geht mit VOLLEN Daten nur an [Mieter, office@], plus zwei Zusatz-Zeilen im Template: `Kontaktweitergabe: maskiert` und `Vermieter-Mail: <stations-adresse>` (zwischen Mobiltelefon und Ort, damit der M7-Regex weiter matcht). NIE auf Content-Masking der Station-Mail zurückbauen — der M7-Parser (EIN Regex) liefe leer → Verfügbarkeits-Mail mit leeren Feldern + NEIN-Draft ohne Mieter-Mail.

**5482694:** M7-Filter lässt office-TO-Mails MIT Marker durch (OR-Gruppe `1.text contains "Kontaktweitergabe: maskiert"`); Parser **M25** zieht `Vermieter-Mail:` → `25.vermietermail`; AddRecord M13 keyed auf `if(25.vermietermail; 25.vermietermail; 1.to[1].address)`; Router **M27**: Route A = M2 unverändert (Filter `25.vermietermail notcontain @`), Route B = **M26** an `{{25.vermietermail}}` — OHNE Telefon-Zeile, OHNE Anrufen/WhatsApp-Buttons, OHNE `mieter=` in den Button-URLs, mit Hinweis „Kontaktdaten senden wir dir automatisch, sobald du bestätigst". Trigger-Query enthält `-subject:"TEST SYSTEM"` → Staging-Tests können den Flow nie auslösen.

**6030776 (Mieter-Mail-Fallback, 16.07.):** Überall wo die Mieter-Mail gebraucht wird gilt `if(1.mieter; 1.mieter; <GetRecord>.mieter)` — M5 Alternativen-Button-URL + M10 NEIN-Draft (40.mieter), M22 JA-Draft + M60 Kontaktdaten-Mail (21.mieter). Alt-Mails MIT `mieter=`-Param laufen unverändert. **M60** war bis 29.07.2026 die Klon-Struktur von M6 und feuerte bei jedem JA — sie ist jetzt aus 6030776 entfernt und lebt als Modul 60 im Freigabe-Szenario **6752917** weiter.

**Fallen:** (1) Beim Deploy der Spring-Seite auf staging/prod hing der Rollout ZWEIMAL an Cluster-Kapazität („0/2 nodes: Insufficient cpu") — alter Pod bediente weiter, obwohl Deploy grün. Nach Backend-Deploys Pod-Image prüfen; hängt er Pending: EINEN alten Pod löschen, bei altem-RS-Pending-Pod Deployment kurz auf replicas=1→2. (2) Test-Rezept für den JA-Fallback: Record in DS 131528 anlegen (Key `vermieter|betreff`), confirm-URL OHNE mieter-Param aufrufen, Kontaktdaten-Mail + Draft prüfen, Records in 131528+131793 löschen. (3) Skripte/Backups: `.secrets/make-5482694-*.js`, `make-6030776-*`, `make-p2-mieter-lookup.js`. Phase 2b ist seit 29.07.2026 GESCHLOSSEN: Die Backend-Vorgangsansicht maskiert serverseitig (`AccessHelper::cfMaskContact`, siehe Skill `camperfuchs-legacy-backend`), und `bemerkung` wird in M2+M26 beim Rendern gefiltert.

## Übergabepunkt: Kontaktdaten erst nach Freigabe (seit 29.07.2026)

Ein JA ist nur eine Verfügbarkeitszusage — keine Buchung, kein Geld. Deshalb hängt die
Kontaktdaten-Mail nicht mehr am JA-Klick.

**Warum kein Automatik-Trigger auf "bezahlt":** Der JA-Draft M22 nennt bei nicht-`onlineBookable`-
Fahrzeugen eine **Überweisung an die Kreissparkasse Limburg**. Ein Geldeingang auf dem Bankkonto
erzeugt kein Systemereignis — `booking_payments` / `online=1` feuern dort nie von allein. Da 82 %
der Anfragen Anfrage-Fahrzeuge sind, wäre eine reine Automatik für genau die Leakage-Fälle
wirkungslos geblieben.

| Baustein | ID / Ort |
|---|---|
| Freigabe-Szenario | **6752917** "CF Kontaktfreigabe", Hook **3469287**, `https://hook.eu1.make.com/33f9mnt861irh0qw2mwuypw79sdp0utg` |
| Freigabe-Button | 6030776 **M6** (JA-Info-Mail an Björn), Link mit `vermieter`/`betreff`/`mieter` (encodeURL) |
| 48h-Rückfall | **6752962** "CF 48h-Rueckfall", alle 3 h |

**Freigabe-Szenario** ist zweistufig wie 6030776 (Scanner-Schutz): ohne `confirm` → Seite mit
Formular-Button, mit `confirm=1` → Danke-Seite + GetRecord (ID 21) + Kontaktdaten-Mail (M60-HTML) +
UpdateRecord. Ops: 2 = Bestätigungsseite, 5 = volle Freigabe-Kette. Der GetRecord behielt bewusst
die ID **21**, damit keine einzige Mapper-Referenz im übernommenen M60-HTML umgeschrieben werden musste.

**Warum ein eigenes Szenario und keine fünfte Route in 6030776:** Ein zweiter Aufruf desselben Hooks
läuft durch die lineare Kette und stirbt an **M17 AddRecord (Duplicate → Ignore)** bei 3 Ops — die
bekannte Falle. Getrennter Hook = getrennte Kette.

**Status-Maschine in DS 131528:** `ja` → `ja_freigegeben` (Freigabe geklickt) bzw. `ja_rueckfall`
(48 h ohne Buchung). `offen` bleibt unangetastet — Nudge 6235553 und M62/M63 arbeiten unverändert.
Der Rückfall greift erst ab Unix-Zeit **1785343000** (Cutoff = Umbau-Zeitpunkt); ohne ihn hätten
beim ersten Lauf 10 echte Vermieter eine "Zeitraum wieder frei"-Mail für längst erledigte Vorgänge
bekommen.

### Datastore-Struktur 444568 war unvollständig (29.07.2026)

5482694 (M13 AddRecord) schrieb seit jeher `telefon`, `ort` und `personen` — die Felder fehlten in
der Struktur und wurden **still verworfen**. Folgen: die Kontaktdaten-Mail mappte `{{21.telefon}}`
und ging **ohne Telefonnummer** raus, und der Personenzahl-Filter im Alt-Vermieter-Picker
(`personen=40.personen`, Szenario 6559455) lief leer. Die Struktur enthält jetzt zusätzlich
`telefon`, `ort`, `personen`, `kontakt_freigegeben`, `rueckfall`.

**Merksatz:** Ein Mapper, der in ein nicht existierendes Datastore-Feld schreibt, wirft keinen
Fehler. Nach jeder Mapper-Erweiterung die Struktur gegenprüfen.

### Make-Fallen, teuer gelernt am 29.07.2026

- **`datastore:SearchRecord` liefert die Felder unter `{{N.data.feld}}`**, nur `{{N.key}}` ist flach.
  Falsche Referenzen sind leer, ein nachgelagerter Filter blockt lautlos, die Ausführung meldet
  trotzdem "Erfolg" mit 1 Op. (Der Bestand macht es in 6030776 M63 schon richtig: `62.data.zeitraum`.)
- **`date:greater` / `date:less` greifen in Filtern NICHT.** Zeitvergleiche numerisch bauen:
  `{{parseNumber(formatDate(2.data.beantwortet; "X"))}}` gegen
  `{{parseNumber(formatDate(addHours(now; -48); "X"))}}`.
- **`notexist` auf Datastore-Feldern funktioniert nicht** → Zustände über ein Status-Feld führen,
  nicht über "Feld leer".
- **Scheduling per API:** `type` muss aus `immediately, indefinitely, once, daily, weekly, monthly,
  yearly, on-demand` kommen; `interval` (Sekunden) ist ein Zusatzfeld. `type:"interval"` wird
  abgelehnt, Webhook-Szenarien brauchen `immediately`.
- **`pg[limit]` max 100** bei `/data-stores/{id}/data` — mit 200 kommt eine leere Liste zurück, was
  wie ein geleerter Datastore aussieht.
- **Blueprint-Edits nie auf dem rohen JSON-String** mit Regex-Ersetzungen, die Backslashes
  enthalten: `\b` ist in JSON ein Steuerzeichen (Backspace) → Parse-Fehler. Rekursiv auf
  Objektebene ersetzen und das Escaping `json.dump` überlassen.

### Bemerkungs-Freitext wird gefiltert (M2 + M26, seit 29.07.2026)

`{{7.bemerkung}}` ist ersetzt durch eine doppelte `replace()`-Formel, die Rufnummern und
E-Mail-Adressen durch `[Kontaktdaten entfernt]` ersetzt (Muster im Projektordner
`01_Architektur-Tech/Maskierung-Phase2b_2026-07-29.md`).

Gefiltert wird erst beim **Rendern** — der M7-Parser hat die Rohdaten längst gelesen, die Kette
bleibt unberührt. ⚠️ **Punkte dürfen NICHT als Trennzeichen in der Telefon-Zeichenklasse stehen**,
sonst schwärzt der Filter Reisezeiträume wie "01.08.2026 - 17.08.2026". Testrezept ohne echte Mail:
Wegwerf-Szenario Webhook → `WebhookRespond`, das die gefilterte Zeichenkette zurückgibt, per curl
alle Muster durchprobieren, danach Szenario + Hook löschen.

## Blueprint validieren + updaten (Schema-Falle)

`scenarios_get` liefert den Blueprint MIT top-level `scheduling` + `interface`. **`validate_blueprint_schema` lehnt beide als „additional properties" ab** → vor validate/update entfernen. Gültiger Blueprint = nur `{ name, flow, metadata }`. `scenarios_update` mit diesem Blueprint bewahrt Scheduling/Interface des Szenarios (separat gespeichert, nicht zurückgesetzt). Ablauf: `scenarios_get` → HTML/IML im Mapper ändern → `scheduling`/`interface` strippen → `validate_blueprint_schema` → `scenarios_update` → `scenarios_get` zurücklesen (HTML/IML intakt? `isinvalid:false`?). ⚠️ **Riesige Mapper-Strings (Signatur in M10!) NIEMALS von Hand neu tippen** — beim manuellen Re-Emit ein Bild-Token abgeschnitten (15.06.). Stattdessen Original sichern, Edits per Python auf den Rohtext (kurze Anker), valides JSON erzeugen, danach Live-Reread + alle opaken Tokens (mail-sig/streak-Links) gegenprüfen.

## Stale-Base-Schutz (teuer gelernt 19./20.07.2026)

Am 19.07. hat ein `scenarios_update` von einer VERALTETEN Blueprint-Basis den M5-Picker-Button,
M60/M61, M50–M53 und die Datastore-Fallbacks **still gelöscht** (am 20.07. restauriert). Regeln:

1. Vor JEDEM `scenarios_update` ein FRISCHES `scenarios_get` als Basis nehmen — nie einen alten
   Download, ein Backup oder einen Blueprint aus einer früheren Session.
2. Modul-ANZAHL gegenprüfen (6030776 = **40 Module** inkl. onerror-Handler — seit dem M60-Ausbau am 29.07.2026, vorher 42) und Marker checken: `m5jc` muss in
   M5 vorkommen (seit Phase 4 nur noch dort; M50=GetRecord, M60 ohne Hook-Link).
3. Pre-Update-Backup des frischen Blueprints nach `outputs/` legen.
4. Nach dem Update Marker + Signatur-Token erneut prüfen: `streak-link.com` 27x, mail-sig 21x
   im Blueprint.

## Test-Rezept (immer mit vermieter=b.dunker@…, nie echte Partner)

**Headless per Sandbox-curl (15.06. erprobt, kein Chrome nötig):**
1. **Stufe 1 (NEIN, Scanner-Simulation):** `curl "https://hook.eu1.make.com/tu2xumx8rhjynvul6l2stjxq7r5mcc55?aktion=nein&vermieter=b.dunker%40camperfuchs.de&betreff=TEST&mieter=b.dunker%40camperfuchs.de&vorname=Karolina"` → muss die **Formular-Seite** (zwei Felder) liefern, keine Aktion. (JA → Button-Seite; Rückfrage → Freitext-Formular „frage".)
2. **Stufe 2 (Formular-Submit):** `curl -G …/tu2… --data-urlencode confirm=1 --data-urlencode aktion=nein --data-urlencode vermieter=b.dunker@… --data-urlencode betreff=TEST --data-urlencode mieter=b.dunker@… --data-urlencode vorname=Karolina --data-urlencode "alt_zeitraum=2. – 9. August" --data-urlencode "alt_fahrzeug=Kulba Rebell"` → Danke-Seite; in Björns Postfach Kalender-/Info-Mail + **Mieter-Entwurf**.
3. **Entwurf prüfen** per Gmail-MCP `list_drafts` (query `subject:"Deine Wohnmobil-Anfrage bei Camperfuchs"`) → `get_thread` (FULL_CONTENT): Alternativ-Absatz korrekt? Auch den **Leer-Fall** (alt-Felder leer) testen → Absatz ohne hängende Satzteile.
4. Aufräumen: Test-Records löschen (`data-store-records_delete` DS 131793 Key `vermieter|betreff|nein`, DS 131528 Key `vermieter|betreff`); Test-Mails/Entwürfe von Björn löschen lassen (Hard-Delete von Mail ist tabu).

⚠️ **Test-Fallen (27.07. teuer gelernt):**
- Zwischen zwei Confirm-Testläufen mit gleichem Key den **131793-Record löschen** — sonst wirft
  M17 AddRecord (Duplicate) → Ignore → Kette stirbt still bei 3 Ops.
- **Ops-Zahl = Diagnose:** 13 = volle JA-Kette (ohne M99), 14 = mit M99, 5 = Stopp vor Router 3,
  3 = Stopp bei M17. `executions_get-detail` liefert bei Webhook-Runs oft nur `{status}` —
  die Ops-Zahl aus `executions_list`/`/logs` ist das Werkzeug.
- Make-REST **PATCH aus der Sandbox braucht einen Browser-User-Agent** (sonst Cloudflare 403
  error 1010); GET geht ohne. Der REST-PATCH-Weg umgeht das MCP-Kontextlimit bei 66k-Blueprints.

Alternativ Chrome-`navigate` auf die Hook-URL (gleiche Stufen). **Mail-Render von 5482694 (M2) ist NICHT sicher selbst testbar** — ein echter Lauf würde die Verfügbarkeits-Mail an einen echten Vermieter schicken. Daher: HTML offline rendern + Blueprint zurücklesen, finale Live-Darstellung an der NÄCHSTEN echten Anfrage prüfen (`executions_list`). ⚠️ `scenarios_run` mit `data` mappt NICHT auf die Webhook-Felder (`{{1.x}}`) → für den Test echten HTTP-Request (curl/Chrome) nutzen, nicht `scenarios_run`.

## WhatsApp-Freitext-Antworten (Szenario 6277699, LIVE seit 15.07.2026)

Vermieter antworten oft im Freitext statt Buttons zu tippen. Das fiel bis 15.07. **still auf den
Boden** (Fall ginbie: 9 Tage keine Reaktion), weil 6277699 nur auf `messages[1].type = button`
filterte. Zusätzlich blieb `status` in DS 131528 auf `rueckfrage` → auch der Nudge (6235553,
sucht `status = offen`) griff nicht mehr.

**Route 2 in 6277699 (`type = text`):** GetRecord DS **137664** (Key = Mobilnr ohne `+`, wird nur
beim Nudge befüllt) → **json:CreateJSON** (Datenstruktur **493593**) → Haiku
(`claude-haiku-4-5`, max_tokens 8, temperature 0, Ein-Wort-Antwort) → Router:

| Klassifikation | Aktion |
|---|---|
| `ja` / `nein` | ruft den confirm-Webhook `tu2xumx8…` → identisch zum Button-Klick, inkl. Kundenentwurf |
| `alternative` / `rueckfrage` / `unklar` | Mail an Björn mit Einschätzung, Wortlaut, wa.me-Link |
| `auto_antwort` | nichts (WhatsApp-Business-Begrüßungen erzeugen kein Rauschen) |

**Prompt-Kern:** Das Modell braucht den KONTEXT (angefragtes Fahrzeug + Zeitraum), sonst ist
„Wir haben nur unseren MF" nicht einzuordnen. `ja`/`nein` NUR bei ausdrücklicher Aussage zum
ANGEFRAGTEN Fahrzeug, im Zweifel `unklar`. 9/10 getestet, Abweichung in die sichere Richtung.
Kosten ~0,50 USD / 1000 Antworten.

**Fallen (teuer gelernt 15.07.):**
- ⛔ **`toJSON` gibt es in Make NICHT.** Freitext sauber ins JSON nur über `json:CreateJSON` +
  Datenstruktur.
- ⛔ **CreateJSON-Mapper-Werte als String (`"8"`/`"0"`) → Anthropic 400** „max_tokens: Input
  should be a valid integer". Müssen echte JSON-Zahlen sein.
- ⛔ **Hook 3270589 ist `web-shared` und hat KEINE URL** → man kann nichts hineinposten, der
  einzige Test ist eine echte WhatsApp. Rezept: Testnummer in DS 137664 eintragen, Template per
  Wegwerf-Szenario an die Nummer senden (öffnet den richtigen Chat), dort Freitext antworten,
  Testeintrag danach löschen.
- ⚠️ **Ops-Zahl verrät die Route:** 3 = Button-Route, 5 = Freitext-Route komplett durchgelaufen.

## Gotchas (teuer gelernt)

- **Scanner-Prefetch ist REAL:** 04.06. 18:05 riefen Provider-Scanner 18 Sek nach Versand alle 3 Button-Links ab (5 Hits/11 Sek) → deshalb der Zwei-Stufen-Flow. NIE auf einstufig zurückbauen. Scanner folgen Mail-Links, klicken aber keine Buttons/Formulare auf Seiten.
- **Gmail 451 „temporarily rejected"** beim ActionSendEmail kommt vor → temporär, Execution ist replayable, einfach erneut auslösen.
- **`switch()`/`if()` in Mappern:** String-Argumente in doppelten Anführungszeichen; KEINE Semikolons in den Strings (Semikolon = Argument-Trenner). Große HTML-Blöcke nie in Formeln stecken. Truthiness: leerer String/0/null = falsy → `if(1.alt_x; …; "")` zeigt nichts, wenn das Feld leer ist (genutzt im NEIN-Alternativ-Absatz).
- **Filter auf leere Webhook-Params:** `exist` reicht NICHT (leerer String existiert) → `text:notequal ""` verwenden (so beim Mieter-Entwurf Modul 10).
- **Datastore-Teilupdate** = `datastore:UpdateRecord`; `AddRecord` mit overwrite ERSETZT den ganzen Record.
- **Mieter-Entwurf ist bewusst OHNE Design-Template** — soll wie eine persönlich von Björn geschriebene Mail wirken (htmlBody + volle Signatur in Braun #783f04). Textregeln: Du-Form, kein Druck/Verknappung, NIE Reservierung anbieten, keine Telefon-CTAs (siehe camperfuchs-brand + Memory-Feedback).
- **Logos von www. laden** (nicht new. — Subdomain verschwindet beim Relaunch). Neue Bilder per WP-REST-API hochladen (Zugang: `.secrets/Claude AP-wordpressI.txt` Zeile 3, User bjoerndunker).
- **Betreff-Kollision im Tracking:** Key `vermieter|betreff` — fragt derselbe Kunde dasselbe Fahrzeug erneut an, überschreibt der neue Versand den alten Record (gewollt: letzte Anfrage zählt).
- Alt-Mails (vor 04.06. abends versendet) haben keine `mieter`/`vorname`-Params → Filter überspringen Entwurf einfach; kein Fehler.

## Typische Aufgaben

- **Template-Text/Design ändern:** Blueprint per `scenarios_get` ziehen, NUR den HTML-String im betreffenden Mapper ändern (5482694 M2 = Verfügbarkeits-Mail, M26 = maskierte Variante (Änderungen in BEIDEN nachziehen!); 6030776 M12 = Button-Bestätigung (nur JA), M20 = NEIN-Formular, M30 = Rückfrage-Formular, M2 = Danke-Seite, M4 = Kalender-Erinnerung, M5 = Björn-Info NEIN, M7 = Björn-Info Rückfrage (mit `frage`), M10 = Mieter-Entwurf), `scheduling`/`interface` strippen, validate, update, zurücklesen, Test-Rezept fahren, Referenz-HTML im Projektordner nachziehen.
- **Alternativ-Absatz/Formular ändern:** Modul 20 (Formular-HTML) bzw. Modul 10 (`if()`-Fragmente) — Truthiness-Regel beachten.
- **Fahrzeug-/Telefon-Button ändern:** nur Modul 2 (Mapper `html`) — siehe Abschnitt „Fahrzeug-Link & Telefon als Buttons".
- **Wer hat nicht reagiert / Quote:** Dashboard-Artefakt öffnen (Tab „Vermieter") oder ad hoc `data-store-records_list` auswerten.
- **Dashboard erweitern:** HTML neu schreiben → `update_artifact` (id `verfuegbarkeits-antworten`). Datenform: Array von `{key, data:{…}}`.

## Manuelle Verfügbarkeitsanfrage OHNE konkretes Fahrzeug (seit 10.07.2026)

Für den umgekehrten Fall: Björn fragt selbst bei einem/mehreren Vermietern an, ob sie ein Fahrzeug für N Personen im Zeitraum X frei haben oder einen Alternativzeitraum anbieten. Kein Make-Flow, kein Tracking (keine Anfrage-ID) — Versand manuell bzw. als Gmail-Entwurf.

- **Vorlage:** `04_Setup-Anleitungen/Mail-Vorlage_Vermieter-Verfuegbarkeitsanfrage.html` — Card-Design, Info-Box (Personen + Zeitraum, KEIN Fahrzeug), 3 Buttons in Flow-Optik (JA grün `#2e7d32` / NEIN rot `#c62828` / „Alternativzeitraum vorschlagen" weiß+braun).
- **Buttons = mailto-Links** an b.dunker@ mit vorbefülltem Betreff/Body (JA: Fahrzeug+Preis-Felder; Alternativ: Fahrzeug, frei von/bis, Preis). Antworten kommen als normale Mail mit eindeutigem Betreff.
- **Platzhalter** `{Vorname}` `{Personenzahl}` `{von}` `{bis}` stecken AUCH in den mailto-Links → Suchen&Ersetzen über die ganze Datei; Datumsformat ohne Leerzeichen (10.08.2026), sonst brechen die Links.
- **⚠️ Gmail-Draft-Gotcha:** Gmail-Compose strippt die CSS-Kurzform `background:` → weiße Schrift wird unsichtbar (Balken/Buttons „verschwinden"). Vorlage ist deshalb tabellenbasiert (`<td bgcolor + background-color>`) — NICHT auf div+background zurückbauen. Gilt für ALLE per create_draft angelegten Card-Mails (Memory `gmail-draft-html-gotcha`).
- **create_draft braucht ≥1 Empfänger** → beim Entwurf-Anlegen Björns eigene Adresse eintragen, vor Versand tauschen. Signatur-Block anhängen (Memory `email-signatur-und-stil`).

## Querverweise

- **`camperfuchs-nein-alternativen-anfragen`** — Alt-Vermieter-Picker „Freie Alternativen anfragen" (eigenes Szenario **6559455**, Hook `m5jc…`).
- **`camperfuchs-kalender-sperre`** — Kalender-Sperr-Automatik auf der NEIN-Danke-Seite (Make 6578305 → `/api/automation/block` auf srv2).
