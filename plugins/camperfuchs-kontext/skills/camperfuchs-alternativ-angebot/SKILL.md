---
name: camperfuchs-alternativ-angebot
description: >
  Alternativ-Angebote fuer Camperfuchs-Mietinteressenten bauen, wenn der Vermieter NEIN sagt oder
  per WhatsApp/Mail Alternativen nennt. IMMER nutzen, wenn ein Kunde nach einer Absage Vorschlaege
  bekommen soll - explizit ("biete dem Kunden X an", "schlag Familie Y was vor", "Vermieter hat
  Alternativen genannt") wie implizit (NEIN-Mail liegt vor, WhatsApp mit Kennzeichen wie
  "HD ME 466", "haben wir sonst was frei?"). Das Alternativen-SUCHEN ist Claudes Job - proaktiv
  freie Fahrzeuge finden, statt nur einen Such-Link zu liefern. Kern-Regeln: Personenzahl aus der
  Anfrage ist PFLICHT-Filter (maxSeats/maxBeds), Card-Design ist Standardlayout,
  zwei Suchen fahren (Vermieter-Standort + Kundenwohnort), Fahrzeug nicht im Bestand ->
  by-landlord pruefen und Einrichtung anbieten. Liefert: Gmail-Entwurf mit Fahrzeug-Deeplinks inkl.
  Zeitraum plus Flexibilitaets-Frage. NICHT fuer den JA/NEIN-Grundflow
  (-> camperfuchs-verfuegbarkeits-flow) oder den Alt-Vermieter-Picker
  (-> camperfuchs-nein-alternativen-anfragen).
metadata:
  type: skill
  scope: camperfuchs-rentanda
---

# Camperfuchs: Alternativ-Angebot mit Fahrzeug-Direktlinks

## Grundregeln

- **Das Suchen ist Claudes Job.** Bei einem Absage-Fall proaktiv konkrete FREIE Fahrzeuge finden
  (Schritt 3b) und ein fertiges Angebot als Gmail-Entwurf bauen, nicht nur einen Such-Link liefern.
- **Personenzahl ist Pflicht, bevor irgendein Fahrzeug vorgeschlagen wird.** Sie steht im Feld
  `Bemerkung` der Formular-Mail, Format `Anzahl Erwachsene: 2 | Anzahl Kinder: 1`. Erst ziehen,
  dann filtern. Nie nach Bauart und Entfernung allein auswaehlen (siehe Falle unten).
- **Card-Design ist das Standardlayout** (Schritt 5), nicht die Signatur-Vorlage.
- **IMMER nach Flexibilitaet fragen.** Am Ende jeder Alternativ-Mail fragen, ob der Reisezeitraum
  flexibel ist, besonders wenn die Alternativen den Wunschzeitraum nicht voll abdecken.
- Ton: **Du**-Anrede, KEIN Druck/Verknappung, KEINE Reservierungs-Angebote, KEIN Telefon-CTA
  (Selbsthilfe per Link), KEINE Gedankenstriche.

## Wann

Vermieter meldet NEIN auf eine Mietanfrage oder nennt (oft per WhatsApp, oft mit Kennzeichen statt
Modellnamen) Alternativ-Fahrzeuge bzw. -Zeitraeume; oder Bjoern sagt "biete Kunde X das Fahrzeug Y
an". Der Kunde soll eine Mail mit konkreten, klickbaren Optionen bekommen.

## Workflow

### 1. Kontext aus Gmail/Datastore holen

Die System-Mail "Wichtig: Neue Mietanfrage von {Kunde}" (von noreply@camperfuchs.de) enthaelt alle
Formulardaten. Pflichtfelder:

- `Fahrzeug`, `Reisezeitraum` (Format `TT-MM-JJJJ bis TT-MM-JJJJ`)
- `Ort` = **Kundenwohnort**; `Standort` = **Vermieter**, nicht verwechseln
- `Vorname`/`Nachname`, `E-mail`
- `Bemerkung` = **Personenzahl** + Freitext-Wunsch des Kunden

Der Freitext in `Bemerkung` ist Gold fuer die Mail (z.B. "Einfach fahren und da bleiben wo es
schoen ist"). Einmal aufgreifen, nicht ignorieren.

Threads sind riesiges HTML (50-175 KB) -> `get_thread` legt den Inhalt in eine Datei; NICHT komplett
lesen, sondern die Felder greppen (HTML strippen, dann `Fahrzeug:/Reisezeitraum:/Ort:/Bemerkung:`).
Schneller Weg fuer Eckdaten: Make-Datastore **131528** (kunde/fahrzeug/zeitraum/mieter/betreff/ort).
IMMER pruefen, ob dem Kunden schon eine persoenliche Mail raus ist (`to:{kundenmail} in:sent`).

### 2. Kennzeichen -> Fahrzeug aufloesen

Vermieter nennen oft Kennzeichen ("HD ME 466"). Mapping im Backend
`https://www.camperfuchs.de/backend/articles` (Kennzeichen, Fahrzeugname, Vermieter/Standort).
Achtung Tippfehler im WhatsApp ("363" statt "463").

### 3. Slug fuer den Deeplink finden

    curl -s "https://www.camperfuchs.de/api/V1/seo/articles/sitemap.xml" | grep -o '<loc>[^<]*</loc>' | sed 's/<\/\?loc>//g' | grep -i {standort}

Liefert `/wohnmobil-mieten/{standort}/{kategorie}/{slug}`. Umlaute/Klammern im Standort bleiben im
Slug (`goergeshausen`, `ehingen-(donau)`) -> im Deeplink URL-encoden (`%C3%B6`, `%28`/`%29`).

### 3b. Freie Fahrzeuge SELBST finden

    curl -s "https://www.camperfuchs.de/api/V1/articles?from=JJJJ-MM-TT&to=JJJJ-MM-TT&address={Ort}&lat={lat}&lon={lon}&size=30"

-> `content[]` je Fahrzeug: `title`, `uri`, `location`, `distanceInKm`, `onlineBookable`,
`availableSlotFrom/To`, `totalPrice`, `rate`, `maxSeats`, `maxBeds`, `subType`. Kundenkoordinaten
per Nominatim geocoden (`nominatim.openstreetmap.org/search?q={ort}&format=json&limit=1&countrycodes=de`,
User-Agent Pflicht, ~1s Ratelimit). Nur die Fahrzeuge eines Vermieters:
`/api/V1/articles/by-landlord?email={vermieter}`.

**Personenfilter ist nicht optional.** Die API hat keinen Personen-Parameter, also lokal filtern:

    maxSeats >= Personenzahl  UND  maxBeds >= Personenzahl

Bei 2 Erwachsenen + 1 Kind also mindestens 3 Sitze mit Gurt und 3 Betten, praktisch fast immer 4/4.
Fehlgriffe, die durchrutschen, wenn man nur auf Bauart filtert (real passiert am 15.07.2026):
VW Grand California 680 = 2 Sitze/2 Betten, Poessl Summit Shine 600 = 3 Sitze aber nur 2 Betten.

**Zwei Suchen fahren, nicht eine:** einmal ab dem urspruenglich gewaehlten **Vermieter-Standort**
(der Kunde hat ihn bewusst gewaehlt, oft wegen der Reiseregion) und einmal ab dem **Kundenwohnort**.
Beides getrennt anbieten, je mit Entfernungsangabe. Der Suchradius ist entfernungsbasiert, die
Trefferzahl unterscheidet sich dadurch stark (Beispiel: 80 Treffer ab Ulm vs. 16 ab Coburg).

Vorauswahl: naechstgelegen, im Wunschzeitraum frei, moeglichst `onlineBookable:true`. Bei
`onlineBookable:false` (= nur Anfrage) verhalten anbieten, zuerst den Vermieter bestaetigen lassen.

### 3c. Kalender-Gegencheck beim absagenden Vermieter

Taucht das abgesagte Fahrzeug in der Suche fuer den Zeitraum noch als frei auf, ist der Kalender
nicht gepflegt. Das ist die Ursache fuer genau diese Absagen. Dann in die Vermietermail einen
freundlichen Kalender-Hinweis aufnehmen (Hinweis-Box), siehe auch die Kalender-Mahnung.

### 4. Deeplink mit Zeitraum bauen

    https://www.camperfuchs.de/wohnmobil-mieten/{standort}/{kategorie}/{slug}?from=JJJJ-MM-TT&to=JJJJ-MM-TT&address={Kundenort}&lat={lat}&lon={lon}

`from`/`to` = der fuer DIESES Fahrzeug passende Zeitraum. `&` im href als `&amp;`. Adresse/Koordinaten
= Kundenwohnort (zentriert die Karte beim Kunden).

### 5. Kundenmail als Gmail-Entwurf bauen (Card-Design)

**Layout: `04_Setup-Anleitungen/Mail-Vorlage_Card-Design.html`** (Bjoerns Favorit, Standard fuer
Kunden-, Vermieter- und Partner-Mails). NICHT die Signatur-Vorlage, die ist nur fuer schlichte
Fliesstext-Mails.

Aufbau fuer ein Alternativ-Angebot: Logo-Kopf -> Titel-Balken ("DEINE WOHNMOBIL-ANFRAGE") -> Absage
in einem Satz ohne Ausreden -> Fahrzeug-Karten in zwei Bloecken mit Zwischenueberschrift (Naehe
Vermieter-Standort / Naehe Wohnort) -> beige Info-Box (#f6f1ea) fuer Sonderfaelle (Vermieter-Angebot
in anderem Zeitraum, Fahrzeug noch nicht online) -> Hinweis-Box (#fbf6ef) mit der Flexibilitaets-Frage
-> brauner CTA-Button (#89521f) auf die Suche mit Zeitraum + Kundenkoordinaten -> "Viele Gruesse /
Bjoern" + Card-Footer statt Signatur.

Fahrzeug-Karte:

    <div style="border:1px solid #e7d9c4;border-radius:6px;padding:12px 16px;margin:0 0 10px">
      <p style="font-size:14px;margin:0 0 4px"><a href="{deeplink}" style="color:#89521f;font-weight:bold;text-decoration:none" target="_blank">{Modellname}</a></p>
      <p style="font-size:13px;color:#484745;margin:0 0 4px">{Bauart, Schlafplaetze, 1-2 Ausstattungsdetails}</p>
      <p style="font-size:12px;color:#b3b1b1;margin:0">{Ort} &middot; {Entfernung} &middot; ab {Preis} pro Tag</p>
    </div>

**Bau-Rezept:** HTML per Python-Skript in eine Datei schreiben, dann einen Subagenten die Datei lesen
und `create_draft` aufrufen lassen (to, subject, `htmlBody` = Dateiinhalt byte-genau, `body` =
Plaintext-Fallback). So bleiben Tokens/Styles unangetastet. Alte Entwuerfe gleichen Betreffs an
denselben Kunden zum Loeschen melden, nie selbst hart loeschen.

### 6. Vermieter nennt ein Fahrzeug, das es bei uns nicht gibt

Gegenpruefen: `curl -s "https://www.camperfuchs.de/api/V1/articles/by-landlord?email={vermieter}"`
listet ALLE Fahrzeuge des Vermieters (id/title/uri/onlineBookable/licensePlate). Fehlt das genannte
Fahrzeug:

- dem Kunden das Fahrzeug trotzdem beilaeufig anbieten, aber ehrlich sagen, dass Bilder und Preis
  nachgereicht werden
- dem Vermieter eine Card-Mail schicken mit zwei Wegen: selbst anlegen (bestehendes Fahrzeug als
  Vorlage) ODER **Bjoern uebernimmt die Einrichtung**, wenn der Vermieter Fotos + Eckdaten schickt.
  Die zweite Option immer aktiv anbieten, sie senkt die Huerde deutlich.

## Fallen

- **Braun-Backgrounds (#89521f) beim Nachbauen immer explizit setzen**, sonst weisser Text auf weiss.
  Liest man eine Card-Mail aus dem Gesendet-Ordner zurueck, fehlen die `background`-Farben teils.
- **Umlaute/typografische Anfuehrungszeichen in Python-Strings als HTML-Entities** schreiben
  (`&bdquo;` `&ldquo;` `&ouml;`), sonst SyntaxError beim Bauen des HTML.
- **Die Suche-API ignoriert unbekannte Query-Parameter still** (`?q=`, `?search=` liefern alle
  Treffer statt zu filtern). Nie annehmen, dass ein Filter greift, sondern `totalElements` pruefen.
- **`size` ist auf 20 gedeckelt**, wenn ohne Zeitraum gesucht wird -> paginieren.
- Links sauber als `https://www.camperfuchs.de/...` (keine google/streak-Redirects).
