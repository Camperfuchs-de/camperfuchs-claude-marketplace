---
name: camperfuchs-kontaktfreigabe
description: Die Kontaktfreigabe-Kette von Camperfuchs — wann der Vermieter die Kontaktdaten des Mietinteressenten bekommt (Mail) und wann das Backend den Vorgang demaskiert. IMMER nutzen bei "Vermieter sieht/bekommt keine Kontaktdaten", "sichtbar nach Zahlungseingang" im Backend, "Kontaktdaten freigeben"-Button, leere oder fehlende Kontaktdaten-Mail nach der Zusage, "Kontaktfreigabe ohne Datensatz", Aenderungen an Make 6752917 (CF Kontaktfreigabe) oder am Endpoint cf-contact-release.php auf srv2, sowie bei "warum ist Anfrage X maskiert und Y nicht". Enthaelt die Maskierungsregel, die Kette (5482694 Datastore, 6030776 Freigabe-Button, 6752917 Router, srv2 AccessHelper + Endpoint), dass die Kontaktdaten-Mail seit 01.08.2026 der Endpoint selbst ueber Mailgun schickt, den Mieter+Vermieter-Fallback, das JWT-Verifikations-Rezept und die Cloudflare-Cache-Falle. NICHT fuer die Maskierung der Spring-Anfrage-Mail (Skill camperfuchs-provisions-leakage) oder Mail-Bounces (camperfuchs-legacy-srv2-mail).
---

# Camperfuchs Kontaktfreigabe

Wer wann die Kontaktdaten des Mietinteressenten sieht. Zwei Schichten, die frueher nicht
zusammenpassten: die **Mail** an den Vermieter und die **Sicht im Backend**. Seit 01.08.2026
haengen beide an derselben Freigabe, und **beide macht der srv2-Endpoint** — Make ruft ihn nur auf.

## Die Regel

`AccessHelper::cfContactIsMasked` auf srv2 (`/home/gaz/rent/src/ApiBundle/Helper/AccessHelper.php`):

1. `ROLE_ADMIN` sieht immer alles.
2. **Neu (01.08.2026):** ist `bookings.meta.cfContactReleased` gesetzt, ist genau dieser Vorgang
   offen — unabhaengig von Typ und Zahlungsstand. Das ist die bewusste Ausnahme.
3. Buchungstyp 1/2/4 (Mietanfrage, angenommen, abgelehnt) = maskiert.
4. Camperfuchs-Buchungen (Typ 3/5, `origin != partner`) bleiben maskiert, **solange kein
   Zahlungseingang** da ist (Regel vom 31.07.2026).

Maskiert heisst: `tel`/`mobile`/`street` tragen den Hinweistext ("sichtbar nach Zahlungseingang"),
`email`/`postal_code`/`city`/`birthday` sind leer, Name bleibt sichtbar, `contactMasked: true`.
Hinweistext NUR in den drei Feldern — Text in einem `type=email`- oder Datumsfeld wuerde das
Speichern im Browser blockieren.

## Die Kette

1. **Make 5482694** (Verfuegbarkeits-Mail) legt den Datastore-131528-Datensatz an
   (Key `vermieter|betreff`) und schreibt dabei `vorgang` (Vorgangsnummer, Parser M28) und
   `link` (die `Details [...]`-URL aus dem Spring-Mailtext, Form `…/backend/booking;id=<id>`).
   Fehlen die Felder, ist das seit 01.08.2026 **nicht mehr toedlich** (siehe Fallback unten).
2. **Make 6030776** JA-Route: Mail an b.dunker mit dem Freigabe-Button
   (Hook `33f9mnt861irh0qw2mwuypw79sdp0utg`). Die Kontaktdaten gehen NICHT automatisch raus.
3. **Make 6752917 "CF Kontaktfreigabe"**: Bestaetigungsseite (Zwei-Stufen-Klick) → GetRecord 21 →
   Router 80. **Beide Routen rufen nur noch den Endpoint** — Make verschickt selbst keine
   Kontaktdaten-Mail mehr (das alte Gmail-Modul 60 ist seit 01.08.2026 raus).
   - **Route A (Datensatz da, Filter `kunde exist`):** Datastore-Update `ja_freigegeben` (63) →
     HTTP-**POST** (82) auf `cf-contact-release.php` mit `id` (aus `21.link`), `nr`, `mieter`
     und `vermieter`. Faellt der Call aus, geht per `onerror` (85) eine Warnmail an b.dunker.
   - **Route B (kein Datensatz, Filter `kunde notexist`):** HTTP-POST (90) auf denselben Endpoint,
     nur mit `mieter` + `vermieter`. Der Endpoint sucht den Vorgang selbst. Warnmail (91) nur noch,
     wenn auch das nicht aufloest.
4. **srv2-Endpoint** `https://www.camperfuchs.de/backend/cf-contact-release.php`
   (Datei `/home/gaz/rentanda/web/backend/`, Schluessel `/usr/local/cf/cf-contact-release.key`,
   Kopie in `.secrets/cf-contact-release-key.txt`). Bootet den Symfony-Kernel, schreibt ueber
   `database_connection`, **baut die Kontaktdaten-Mail selbst und verschickt sie ueber Mailgun**.

## Der Endpoint (Stand 01.08.2026)

Parameter: `key` (Pflicht), dazu **`id`** (bookingId) ODER **`nr`** (Vorgangsnummer) ODER
**`mieter=<mail>` + `vermieter=<mail>`**. Optional `undo=1`, `nomail=1` (nur freigeben, keine Mail),
`to=<mail>` (abweichender Empfaenger), `by=<quelle>` fuers Log.

**Fallback-Aufloesung** (wenn weder `id` noch `nr`): Buchungen mit `bookings.email = mieter`,
`cancelled IS NULL`, juenger als 180 Tage, Station ueber `stations.email/emailzwei = vermieter`;
**Vorrang hat der Vorgang mit `meta.vermieterDecision = "ja"`**, sonst der neueste. Antwort und Log
tragen `via=` (`id` | `nr` | `mieter+zusage` | `mieter+neuester`), `cand=`, `mail=`, `to=`.

**Mailweg:** `mail_service` → MailHelper → Swift → **Mailgun EU** (`smtp.eu.mailgun.org`,
`mg.camperfuchs.de`), From `noreply@camperfuchs.de`, Reply-To `office@camperfuchs.de`. Fahrzeugname
aus `articles.short_name`, sonst der SEO-Titel hinter dem ersten `": "`, plus Kennzeichen.
Backup der Vorversion: `cf-contact-release.php.bak-mailgun-20260801`.

Seit 09.09.2026 traegt die Mail zusaetzlich die Mailgun-Variable `cf_b` (8. Argument von
`MailHelper::send`, `array('cf_b' => (int) $row['id'])`). Damit steht die Vorgangs-ID in
`mail_evt.cfb` und jedes Zustell-Ereignis ist dem Vorgang exakt zugeordnet — vorher hing es
nur an der Empfaengeradresse.

## Waechter cf-freigabe-watch.php (seit 01.08.2026)

`/usr/local/cf/cf-freigabe-watch.php`, Cron taeglich 9:45 (`/etc/cron.d/cf-freigabe-watch`),
Tabelle `cf_freigabe_watch` (PK `booking_id`+`kind`, Wiedervorlage 7 Tage). **Standard ist DRY-RUN**,
Versand nur mit `--live`, `--all` hebt die Wiedervorlage auf. Zwei Bloecke in einer Sammelmail an
b.dunker:

- **Block A "Freigabe fehlt":** `meta.vermieterDecision = "ja"`, **Zahlungseingang > 1 EUR** (am
  Vorgang oder an einer ueberlappenden Buchung desselben Mieters), aber kein `cfContactReleased`.
  Ohne Geld wird bewusst NICHT gemeldet - dann ist das Warten richtig. Je Treffer ein Button auf den
  **Make-Hook** (Zwei-Stufen-Bestaetigung), damit **kein Schluessel in der Mail steht**.
- **Block B "Mail nicht zugestellt":** Freigaben der letzten 14 Tage gegen den Worker
  `cf-mailstatus`. **Seit 09.09.2026 ueber `/evt-peek?rec=<adresse>&since=<ts>`** (Auth
  `X-Comm-Key`, Schluessel `/usr/local/cf/cf-comm.key`) — der liest `mail_evt` und haelt jedes
  Ereignis einzeln. `/status?recipient=` (JWT fuer uid 1006) bleibt nur noch Rueckfallebene, falls
  `/evt-peek` keine Auskunft gibt. Kein `delivered` seit der Freigabe oder ein `permanent_fail`
  -> Meldung. Antwortet der Worker gar nicht, wird NICHTS gemeldet (eine Stoerung darf keinen
  Fehlalarm ausloesen).

⚠️ **Block B prueft `meta.cfContactMailTo`, NICHT `stations.email`.** Im ersten Anlauf nahm er die
Stationsadresse an und meldete sofort zwei Vorgaenge als "nicht zugestellt", bei denen die Mail nie
dorthin ging (Testversand mit `to=`, bzw. `nomail=1`). Deshalb schreibt der Endpoint nach
erfolgreichem Versand `cfContactMailTo` + `cfContactMailAt` in die meta. Freigaben von vor dem
01.08.2026 haben den Vermerk nicht und werden uebersprungen.

Das Zustell-Badge aus der Dokumentenliste (Skill `camperfuchs-mailstatus`) geht hier NICHT: es haengt
an `bookings/{id}/documents`, und die Kontaktdaten-Mail ist kein Dokument. Der Waechter ist der Ersatz.

## Haeufige Faelle

- **"Vermieter sieht/bekommt die Daten nicht"** → `tail /var/log/cf-contact-release.log`. Dort steht
  jetzt auch, ob und wohin die Mail ging (`mail=1 to=…`). Kein Eintrag = der Call kam nie an
  (Make-Modul, Filter oder Cache — siehe Fallen).
- **Alter Vorgang ohne `link`/`vorgang`** → Endpoint von Hand mit `id=<bookingId>` aufrufen.
- **Freigabe zurueckziehen** → derselbe Aufruf mit `undo=1` (schickt keine Mail).
- **Mieter hat mehrere Anfragen beim selben Vermieter** → der Fallback nimmt die mit der Zusage.
  Sind mehrere zugesagt, den zweiten Vorgang zusaetzlich per `id=` freigeben.

## Verifikation (nie behaupten, immer messen)

```bash
# JWT fuer einen Nicht-Admin-Nutzer der Station selbst signieren
php -r '$h=rtrim(strtr(base64_encode(json_encode(array("alg"=>"RS256","typ"=>"JWT"))),"+/","-_"),"=");
$p=rtrim(strtr(base64_encode(json_encode(array("uid"=>37600,"exp"=>time()+3600))),"+/","-_"),"=");
$k=openssl_pkey_get_private(file_get_contents("/home/gaz/rent/jwt/key.priv"));
openssl_sign($h.".".$p,$s,$k,"sha256");
echo $h.".".$p.".".rtrim(strtr(base64_encode($s),"+/","-_"),"=");'
curl -s --resolve www.camperfuchs.de:443:127.0.0.1 -k -H "X-Token: $T" \
  https://www.camperfuchs.de/api/bookings/<id> | grep -o '"contactMasked":[a-z]*'
```

Endpoint testen, ohne jemanden anzuschreiben: `-d "nomail=1"` bzw. `-d "to=b.dunker@camperfuchs.de"`.
Ganze Kette testen: Hook mit `?confirm=1&vermieter=…&betreff=…&mieter=…` aufrufen, danach Log lesen.
Fuer Route A vorher einen Datastore-Datensatz anlegen und hinterher wieder loeschen.

⚠️ **`b.dunker@camperfuchs.de` (User 1006) ist ROLE_ADMIN und sieht IMMER alles.** Wer damit testet,
misst nichts. Einen Nicht-Admin-Nutzer der Station aus `user_stations` nehmen.

## Fallen

- **Cloudflare cacht GET-Endpoints unter camperfuchs.de.** Ein zweiter Aufruf derselben URL kam am
  01.08. als identische Erfolgs-Antwort zurueck, ohne PHP zu erreichen: Log leer, DB unveraendert.
  Deshalb `Cache-Control: no-store` im Endpoint UND Aufruf per POST. Eine `{"ok":true}`-Antwort ist
  kein Beweis — immer gegen Log oder DB pruefen.
- **Die alte Version loggte nur Erfolge.** Ein 400/404 (leere `id`, leere `nr`) hinterliess gar
  nichts — genau so blieb am 01.08. eine Freigabe unbemerkt aus, obwohl die Mail rausging.
  Jetzt wird auch `MISS` geloggt.
- **Datastore-Key ist `vermieter|betreff`.** Zwei Anfragen desselben Mieters beim selben Vermieter
  tragen denselben Betreff → nur EIN Datensatz. Deshalb der DB-Fallback.
- **DB ist DO-managed MySQL**, der `mysql`-Client braucht `-P25060`, sonst haengt er stumm.
- **Perf-Schnellpfade umgehen die Maskierung.** Wer im Backend einen neuen Lesepfad baut, der das
  JSON von Hand zusammensetzt statt den Jsoner zu nutzen, liefert unmaskiert aus (so passiert in
  `cfLeanBookingList`). Bei jedem neuen Lesepfad `cfMaskContact` pruefen.
- ⚠️ **`/status` verliert Zustell-Ereignisse: `mail_rec` dedupliziert 15 Minuten.** `recMerge`
  im Worker verwirft ein Ereignis, wenn zum selben Empfaenger schon eines desselben Typs binnen
  `DEDUPE_S` (900 s) vorliegt. Beim Buchungsabschluss gehen "Zahlung eingegangen" und die
  Kontaktdaten-Mail in DERSELBEN Sekunde raus — eine der beiden fiel dort immer heraus. Am
  08.09.2026 meldete Block B deshalb Vorgang 1V0RGT als "nicht zugestellt", obwohl Mailgun
  `250 2.1.5 OK delivered` protokolliert hatte und der Vermieter die Mail sogar geoeffnet hatte.
  Fuer die Frage "ist DIESE eine Mail angekommen?" nie `/status` nehmen, sondern `/evt-peek`
  (liest `mail_evt`, liefert Betreff und Message-ID mit).
- ⚠️ **Ein zweiter Aufruf des Endpoints verschob frueher die Freigabezeit.** Bis 09.09.2026 setzte
  JEDER Aufruf `cfContactReleased = jetzt`, auch bei `already=true` (Nachversand, abweichender
  Empfaenger per `to=`, Test). Der Waechter sucht Zustell-Ereignisse ab genau diesem Zeitpunkt —
  also ab einem Moment, zu dem keine Mail mehr lief — und meldete prompt "nicht zugestellt".
  Seitdem bleibt die Erstfreigabe stehen, Wiederholungen landen in `cfContactReleasedAgainAt` /
  `cfContactReleasedAgainBy`. Wer mit einer aelteren Fassung testet, baut sich den Fehlalarm selbst.
- **srv2-Aenderungen sind nicht in Azure-master** — Live-Datei ziehen, Backup, `php -l`.
  Zugangsweg siehe Skill `camperfuchs-legacy-srv2-mail`.

## Rollback

Endpoint-Datei aus `cf-contact-release.php.bak-mailgun-20260801` zurueckspielen (dann verschickt
Make wieder keine Mail — Modul 60 muesste in 6752917 neu angelegt werden), den
`cfContactReleased`-Block im AccessHelper entfernen
(Backup `AccessHelper.php.bak-cfrelease-*`).
