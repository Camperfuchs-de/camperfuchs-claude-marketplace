---
name: camperfuchs-verfuegbarkeits-flow
description: Betrieb, Änderung und Troubleshooting des Camperfuchs Vermieter-Verfügbarkeits-Flows (Make-Szenarien 5482694 + 6030776, live seit 04.06.2026) — Verfügbarkeits-Mail mit JA/NEIN/Rückfrage-Buttons + Info-Buttons (Fahrzeug ansehen / anrufen), zweistufige Bestätigung gegen Scanner-Fehlklicks, automatischer Gmail-Entwurf an Mietinteressenten bei NEIN (optional mit Alternativ-Zeitraum/-Fahrzeug), Antwort-Tracking im Datastore + Live-Dashboard. Diese Skill IMMER nutzen bei Fragen rund um den Flow — explizit ('Verfügbarkeits-Mail ändern', 'Template anpassen', 'Vermieter-Buttons', 'Bestätigungs-Seite', 'Antwort-Tracking', 'Szenario 5482694/6030776', 'Mieter-Entwurf bei Nein', 'Alternative anbieten') ebenso wie implizit ('Vermieter sagt er hat geklickt aber nichts passiert', 'doppelte Antworten von einem Vermieter', 'Kunde hat keine Antwort bekommen', 'wer hat nicht reagiert', 'Mail-Design anpassen'). Enthält System-Landkarte (alle IDs), Test-Rezepte und teuer gelernte Gotchas.
---

# Camperfuchs Verfügbarkeits-Flow (Vermieter-Buttons + Tracking)

> **NEU (14.07.2026) — eigene Skill für "Alternativen anfragen":** Der Button "Freie Alternativen anfragen" in der NEIN-Info-Mail (Modul 5), die Picker-Seite mit freien Fahrzeugen + Filtern (Personen/minBeds, Bauart, Preis, Haustiere, Umkreis), der direkte Anfrage-Versand an den jeweiligen Alt-Vermieter und der Backend-Endpoint `landlord-contact` sind in einem EIGENEN Make-Szenario **6559455** (Hook `m5jc…`) + Backend. Dafür die Skill **`camperfuchs-nein-alternativen-anfragen`** nutzen. Hier (5482694/6030776) geht es um den Grund-Flow (JA/NEIN/Rückfrage, Tracking, Mieter-Entwurf, Vermieter-eigener Picker Modul 20).

Arbeitsweise (chirurgische Blueprint-Edits, validate vor update) steht in `camperfuchs-make` — die gilt hier immer mit. ⚠️ Korrektur 15.06.: der Make-**Hook** `hook.eu1.make.com/…` IST aus der Sandbox per `curl` erreichbar (siehe Test-Rezept), auch wenn die make.com-**App/API** es nicht ist.

## System-Landkarte (Stand 15.06.2026)

**Flow:** Neue Mietanfrage (Mail von noreply@) → **5482694 „Integration Gmail"** schickt dem Vermieter die Verfügbarkeits-Mail mit 3 Antwort-Button-Links + 2 Info-Buttons + loggt `status=offen` → Klick landet bei **6030776 „Vermieter Verfügbarkeit – Button-Antworten"** (Webhook `3164869`, URL `https://hook.eu1.make.com/tu2xumx8rhjynvul6l2stjxq7r5mcc55`).

**6030776 ist ZWEISTUFIG** (Scanner-Schutz, seit 04.06. ~20 Uhr; Router 11 hat seit 23.06. VIER Routen):
- ohne `confirm`-Param: bei **NEIN → Modul 20 Fahrzeug-Picker-Formular** (lädt per JS die freien Fahrzeuge des Vermieters als antippbare Radio-Liste via `by-landlord` — inkl. Kennzeichen hinter dem Namen — plus Freitext-Fallback + „Alternativer Zeitraum"); bei **Rückfrage → Modul 30 Freitext-Formular** (Textfeld „Deine Frage oder Anmerkung" → Param `frage`); bei **JA → Modul 12 Button-Seite**. Alle drei rufen dieselbe URL mit `confirm=1` + allen Params (+ ggf. `alt_zeitraum`/`alt_fahrzeug` aus M20 bzw. `frage` aus M30) auf. Filter: Modul 12 = `confirm notexist` UND `aktion text:notequal nein` UND `aktion text:notequal rueckfrage` (= nur JA + Fallback); Modul 20 = `confirm notexist` UND `aktion text:equal nein`; Modul 30 = `confirm notexist` UND `aktion text:equal rueckfrage`.
- mit `confirm=1` → Modul 2 Danke-Seite → Modul 17 AddRecord (geklickt) → Modul 13 UpdateRecord (Tracking) → Modul 8 DeleteRecord (24h-Reminder-Stopp, Datastore 124997) → Router 3:
  - **NEIN**: Modul 4 Kalender-Erinnerung an Vermieter (Backend-Button → `www.camperfuchs.de/backend/`) + Modul 5 Info an Björn (zeigt Alternativ-Zeitraum/-Fahrzeug im Beige-Block) + **Modul 10 Gmail-ENTWURF an den Mietinteressenten** (Betreff „Deine Wohnmobil-Anfrage bei Camperfuchs", personalisiert mit `{{1.vorname}}`, volle Signatur, **conditional Alternativ-Absatz** — Vorlage: `04_Setup-Anleitungen/Gmail-Signatur-Vorlage.html`)
  - **JA** (Modul 6): Info-Mail an Björn
  - **Rückfrage** (Modul 7): Info-Mail an Björn — zeigt jetzt den Vermieter-Freitext im Beige-Block „Frage des Vermieters" via `{{if(1.frage; 1.frage; "(keine Angabe …)")}}` (`white-space:pre-wrap`)

**Webhook-Params:** `aktion` (ja|nein|rueckfrage), `vermieter`, `betreff`, `mieter` (Mieter-E-Mail), `vorname`, `confirm`, **`alt_zeitraum`/`alt_fahrzeug`** (optional, nur aus dem NEIN-Formular Modul 20), **`frage`** (optional, nur aus dem Rückfrage-Formular Modul 30). Neue Params kommen dynamisch durch (kein `metadata.interface`-Eintrag nötig — vgl. `alt_*`/`frage`).

**Tracking:** Datastore **131528** „Verfügbarkeits-Tracking" (Struktur 444568), Key = `vermieter|betreff`. Felder: vermieter, kunde, fahrzeug, zeitraum, mieter, betreff, status (offen|ja|nein|rueckfrage), gesendet, beantwortet. 5482694 schreibt AddRecord (overwrite, onerror Ignore); 6030776 Confirm-Route UpdateRecord (Teilupdate, onerror Ignore). „offen" = nie bestätigt geklickt. (Zweiter „geklickt"-Datastore **131793**, Key `vermieter|betreff|aktion`.)

**Dashboard:** Cowork-Artefakt `verfuegbarkeits-antworten` — liest Datastore live via Make-MCP `data-store-records_list` (dataStoreId 131528). Zwei Tabs: Anfragen (KPIs + Filter-Tabelle) und Vermieter (pro Vermieter: Anfragen, JA/NEIN/Rückfrage/Offen, Antwortquote, Ø Reaktionszeit). Ändern via `update_artifact`.

**Design (von new.camperfuchs.de, Kadence-Palette):** weißer Header mit Badge-Logo `www.camperfuchs.de/wp-content/uploads/2026/06/CF_Logo_Badge_320x280.png` (Media-ID 19625), Titel-Band Braun `#89521f` weiß UPPERCASE, Datenblock Beige `#efeae6` (Kunde, Fahrzeug, Reisezeitraum, Bemerkung), darunter **2 braune Info-Buttons `#89521f`** („Fahrzeug ansehen" / „{{telefon}} anrufen", OHNE Emoji-Icons — Björn-Wunsch 08.06.), Text Anthrazit `#28383d`/`#484745`, dunkler Footer `#202020` mit weißem Logo `…/CF_Logo_Header_White.png` (ID 19626), Antwort-Buttons JA `#2e7d32` / NEIN `#c62828` / Rückfrage weiß mit Braun-Outline. Formular-Seite (Modul 20) übernimmt dieselbe Palette. Referenz-HTML: `01_Architektur-Tech/Vermieter-Verfuegbarkeitsmail_Buttons_2026-06-08_Vorschau.html`, `01_Architektur-Tech/Verfuegbarkeit-NEIN-Formular_2026-06-15_Vorschau.html`.

**Connections:** Gmail v4 `6998308` (Trigger, sendAnEmail, createADraft) · Google Restricted `7458024` (ActionSendEmail v2).

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

## Blueprint validieren + updaten (Schema-Falle)

`scenarios_get` liefert den Blueprint MIT top-level `scheduling` + `interface`. **`validate_blueprint_schema` lehnt beide als „additional properties" ab** → vor validate/update entfernen. Gültiger Blueprint = nur `{ name, flow, metadata }`. `scenarios_update` mit diesem Blueprint bewahrt Scheduling/Interface des Szenarios (separat gespeichert, nicht zurückgesetzt). Ablauf: `scenarios_get` → HTML/IML im Mapper ändern → `scheduling`/`interface` strippen → `validate_blueprint_schema` → `scenarios_update` → `scenarios_get` zurücklesen (HTML/IML intakt? `isinvalid:false`?). ⚠️ **Riesige Mapper-Strings (Signatur in M10!) NIEMALS von Hand neu tippen** — beim manuellen Re-Emit ein Bild-Token abgeschnitten (15.06.). Stattdessen Original sichern, Edits per Python auf den Rohtext (kurze Anker), valides JSON erzeugen, danach Live-Reread + alle opaken Tokens (mail-sig/streak-Links) gegenprüfen.

## Test-Rezept (immer mit vermieter=b.dunker@…, nie echte Partner)

**Headless per Sandbox-curl (15.06. erprobt, kein Chrome nötig):**
1. **Stufe 1 (NEIN, Scanner-Simulation):** `curl "https://hook.eu1.make.com/tu2xumx8rhjynvul6l2stjxq7r5mcc55?aktion=nein&vermieter=b.dunker%40camperfuchs.de&betreff=TEST&mieter=b.dunker%40camperfuchs.de&vorname=Karolina"` → muss die **Formular-Seite** (zwei Felder) liefern, keine Aktion. (JA → Button-Seite; Rückfrage → Freitext-Formular „frage".)
2. **Stufe 2 (Formular-Submit):** `curl -G …/tu2… --data-urlencode confirm=1 --data-urlencode aktion=nein --data-urlencode vermieter=b.dunker@… --data-urlencode betreff=TEST --data-urlencode mieter=b.dunker@… --data-urlencode vorname=Karolina --data-urlencode "alt_zeitraum=2. – 9. August" --data-urlencode "alt_fahrzeug=Kulba Rebell"` → Danke-Seite; in Björns Postfach Kalender-/Info-Mail + **Mieter-Entwurf**.
3. **Entwurf prüfen** per Gmail-MCP `list_drafts` (query `subject:"Deine Wohnmobil-Anfrage bei Camperfuchs"`) → `get_thread` (FULL_CONTENT): Alternativ-Absatz korrekt? Auch den **Leer-Fall** (alt-Felder leer) testen → Absatz ohne hängende Satzteile.
4. Aufräumen: Test-Records löschen (`data-store-records_delete` DS 131793 Key `vermieter|betreff|nein`, DS 131528 Key `vermieter|betreff`); Test-Mails/Entwürfe von Björn löschen lassen (Hard-Delete von Mail ist tabu).

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

- **Template-Text/Design ändern:** Blueprint per `scenarios_get` ziehen, NUR den HTML-String im betreffenden Mapper ändern (5482694 M2 = Verfügbarkeits-Mail; 6030776 M12 = Button-Bestätigung (nur JA), M20 = NEIN-Formular, M30 = Rückfrage-Formular, M2 = Danke-Seite, M4 = Kalender-Erinnerung, M5 = Björn-Info NEIN, M7 = Björn-Info Rückfrage (mit `frage`), M10 = Mieter-Entwurf), `scheduling`/`interface` strippen, validate, update, zurücklesen, Test-Rezept fahren, Referenz-HTML im Projektordner nachziehen.
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
