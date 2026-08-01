---
name: camperfuchs-kontaktfreigabe
description: Die Kontaktfreigabe-Kette von Camperfuchs — wann der Vermieter die Kontaktdaten des Mietinteressenten bekommt (Mail) und wann das Backend den Vorgang demaskiert. IMMER nutzen bei "Vermieter sieht keine Kontaktdaten", "sichtbar nach Zahlungseingang" im Backend, "Kontaktdaten freigeben"-Button, leere oder fehlende Kontaktdaten-Mail nach der Zusage, Link zum Vorgang in der Freigabe-Mail, Aenderungen an Make 6752917 (CF Kontaktfreigabe) oder am Endpoint cf-contact-release.php auf srv2, sowie bei der Frage "warum ist Anfrage X maskiert und Y nicht". Enthaelt die Maskierungsregel, die vier Bausteine der Kette (5482694 Datastore-Felder, 6030776 Freigabe-Button, 6752917 Router, srv2 AccessHelper + Endpoint), das Verifikations-Rezept mit selbst signiertem JWT und die Cloudflare-Cache-Falle. NICHT fuer die Maskierung der Spring-Anfrage-Mail selbst (Skill camperfuchs-provisions-leakage) oder Mail-Bounces (camperfuchs-legacy-srv2-mail).
---

# Camperfuchs Kontaktfreigabe

Wer wann die Kontaktdaten des Mietinteressenten sieht. Zwei Schichten, die frueher nicht
zusammenpassten: die **Mail** an den Vermieter und die **Sicht im Backend**. Seit 01.08.2026
haengen sie an derselben Freigabe.

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
   Ohne diese beiden Felder kann spaeter weder verlinkt noch freigegeben werden.
2. **Make 6030776** JA-Route: Mail an b.dunker mit dem Freigabe-Button
   (Hook `33f9mnt861irh0qw2mwuypw79sdp0utg`). Die Kontaktdaten gehen NICHT automatisch raus.
3. **Make 6752917 "CF Kontaktfreigabe"**: Bestaetigungsseite (Zwei-Stufen-Klick) → GetRecord 21 →
   Router 80.
   - **Route A (Datensatz da):** Kontaktdaten-Mail an den Vermieter inkl. Button
     "Vorgang im Backend oeffnen" → Datastore-Update `ja_freigegeben` → HTTP-**POST** auf
     `cf-contact-release.php`. Faellt der Call aus, geht per `onerror` eine Warnmail an b.dunker,
     danach `Ignore`.
   - **Route B (kein Datensatz):** KEINE Vermieter-Mail, nur Warnmail an b.dunker. Diese Route
     existiert, weil sonst eine Mail mit lauter leeren Feldern rausgeht (passiert am 01.08. 01:29).
4. **srv2-Endpoint** `https://www.camperfuchs.de/backend/cf-contact-release.php`
   (Datei `/home/gaz/rentanda/web/backend/`, Schluessel `/usr/local/cf/cf-contact-release.key`,
   Kopie in `.secrets/cf-contact-release-key.txt`). Parameter: `key`, dazu `id` (bookingId) ODER
   `nr` (Vorgangsnummer), optional `undo=1` und `by=` fuers Log `/var/log/cf-contact-release.log`.
   Bootet den Symfony-Kernel und schreibt ueber `database_connection`, kein eigener DB-Zugang.

## Haeufige Faelle

- **"Vermieter sieht die Daten nicht, obwohl er die Mail hat"** → pruefen, ob der Endpoint gelaufen
  ist: `tail /var/log/cf-contact-release.log`. Kein Eintrag = Route A ist nicht bis zum HTTP-Modul
  gekommen oder der Call wurde gecacht (siehe Falle unten).
- **Mail mit leeren Feldern** → GetRecord fand keinen Datensatz. Key ist `vermieter|betreff`,
  Betreff mit Gedankenstrich/Umlaut in der Button-URL ist der uebliche Verdaechtige.
- **Alter Vorgang ohne `link`/`vorgang`** → Endpoint von Hand mit `id=<bookingId>` aufrufen.
- **Freigabe zurueckziehen** → derselbe Aufruf mit `undo=1`.

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

⚠️ **`b.dunker@camperfuchs.de` (User 1006) ist ROLE_ADMIN und sieht IMMER alles.** Wer damit testet,
misst nichts. Einen Nicht-Admin-Nutzer der Station aus `user_stations` nehmen.

## Fallen

- **Cloudflare cacht GET-Endpoints unter camperfuchs.de.** Ein zweiter Aufruf derselben URL kam am
  01.08. als identische Erfolgs-Antwort zurueck, ohne PHP zu erreichen: Log leer, DB unveraendert.
  Deshalb `Cache-Control: no-store` im Endpoint UND Aufruf per POST. Eine `{"ok":true}`-Antwort ist
  kein Beweis — immer gegen Log oder DB pruefen.
- **DB ist DO-managed MySQL**, der `mysql`-Client braucht `-P25060`, sonst haengt er stumm.
- **Perf-Schnellpfade umgehen die Maskierung.** Wer im Backend einen neuen Lesepfad baut, der das
  JSON von Hand zusammensetzt statt den Jsoner zu nutzen, liefert unmaskiert aus (so passiert in
  `cfLeanBookingList`). Bei jedem neuen Lesepfad `cfMaskContact` pruefen.
- **srv2-Aenderungen sind nicht in Azure-master** — Live-Datei ziehen, Backup, `php -l`,
  `service php5-fpm reload`. Zugangsweg siehe Skill `camperfuchs-legacy-srv2-mail`.

## Rollback

Endpoint-Datei loeschen, den `cfContactReleased`-Block im AccessHelper entfernen
(Backup `AccessHelper.php.bak-cfrelease-*`), in Make 6752917 den Router 80 wieder auf die alte
Kette 60 → 63 ziehen.
