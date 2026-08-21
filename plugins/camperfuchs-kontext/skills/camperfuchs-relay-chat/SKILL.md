---
name: camperfuchs-relay-chat
description: >-
  System-Landkarte und Fallen des Camperfuchs Relay-Chats — die maskierte Vermittlung zwischen
  Vermieter und Mietinteressent (Cloudflare-Worker cf-mailstatus, Aliasse chat+/partner+/antwort+
  @mg.camperfuchs.de, D1-Tabellen chat_map/chat_partner/chat_out, Seite /backend/nachrichten).
  IMMER nutzen, wenn am Chat, an den Relay-Mails oder an den Mailgun-Routen gearbeitet wird —
  explizit („Relay-Chat", „maskierte Nachricht", „chat+ Alias", „Nachrichten-Seite", „Anhang im
  Chat", „Mailgun-Route", „comm_log") wie implizit („Kundenantwort kommt nicht an", „der Vermieter
  hat nie geantwortet", „Bild fehlt im Chat", „Verlauf ist unvollständig", „warum steht der Vorgang
  zweimal in der Liste"). Enthält die teuerste Lehre des Projekts: eine zu enge Mailgun-Route hat
  wochenlang JEDE Kundenantwort verschluckt, ohne eine einzige Fehlermeldung.
---

# Camperfuchs Relay-Chat — Landkarte und Fallen

Der Relay-Chat vermittelt zwischen Vermieter und Mietinteressent, ohne dass die beiden die
Kontaktdaten des anderen sehen. Erst mit der verbindlichen Buchung werden sie ausgetauscht.
Das ist keine Bequemlichkeit, sondern die Provisionsgrundlage.

## Die Teile

| Teil | Was es tut |
|---|---|
| Worker `cf-mailstatus` | Rendert die Chat-Seiten, nimmt Mails an, verschickt die Relay-Mails |
| `chat+<id>@mg.camperfuchs.de` | Der Kunde schreibt an den Vermieter |
| `partner+<id>@mg.camperfuchs.de` | Der Vermieter schreibt an den Kunden |
| `antwort+<id>@mg.camperfuchs.de` | Der Kunde antwortet dem Camperfuchs-Team |
| D1 `chat_map` | Wer ist Mieter, wer Vermieter, Status des Vorgangs |
| D1 `chat_partner` | Der eigentliche Verlauf, je Eintrag `d: v2m` oder `m2v` |
| D1 `comm_log` | Vorgangs-Cockpit: was ist wann an wen rausgegangen |
| `/backend/nachrichten` | Die Chat-Oberfläche, ebenfalls aus dem Worker, NICHT aus der Angular-App |

Magic-Links (`/t?b=…&r=m|v&s=…`) geben Mieter und Vermieter Zugang ohne Login. Die Signatur ist
ein HMAC über `t|<vorgang>|<rolle>`.

## 🚨 Die teuerste Lehre: die Route ist Teil des Systems

Die Mailgun-Routen matchten anfangs nur numerische Vorgangsschlüssel
(`^chat\+[0-9]+@mg\.camperfuchs\.de$`). Der Reply-To der ausgehenden Mail trug aber die
Buchungsnummer (`chat+RGTSVF@`), weil der Vorgang aus dem Backend-Chat mit der Nummer hereinkam.

Folge: keine Route griff, der `catch_all()` schob die Mail still ins Sammelpostfach, der Worker
sah sie nie. Kein Eintrag, kein Log, kein Alarm. Eine Mietinteressentin schrieb dreimal, schickte
zwei Fotos, bekam nie eine Antwort und sagte ab. Der Vermieter erfuhr nichts davon.

**Regeln:**

- Fehlt im Chat eine Nachricht, IMMER zuerst prüfen, ob die Mailgun-Route gegriffen hat.
  Erst danach Worker, D1 oder Make verdächtigen.
- Neue Aliasse immer mit `[A-Za-z0-9]+` anlegen, nie mit `[0-9]+`.
- Es gibt eine Route mit Priorität 1 auf `.*@mg\.camperfuchs\.de`, die alles Unbekannte an den
  Worker schickt. Der meldet es sofort per Mail und schreibt `comm_log.channel='unrouted'`.
  Diese Route ersetzt einen Überwachungs-Task und darf nicht gelöscht werden.

Verallgemeinert: **ein stiller Fallback ist gefährlicher als ein lauter Fehler.** Wo etwas
weitergereicht wird, muss der Fall „passt zu nichts" eine Meldung erzeugen.

## Vorgangs-Schlüssel: die numerische ID ist die Wahrheit

Derselbe Vorgang kommt mal als Buchungsnummer (`QFMK1Y`), mal als numerische ID (`533621`).
Make schreibt mit der Nummer, das Backend verlinkt mit der ID. Ungefiltert entstehen daraus
gespaltene Verläufe: derselbe Kunde zweimal in der Liste, je die Hälfte der Nachrichten.

Der Worker normalisiert deshalb jeden eingehenden Schlüssel: rein numerisch → fertig, sonst
Nachschlagen in `bk_alias`, sonst einmalig beim Backend auflösen und merken. Wer einen neuen
Eingang baut, muss diese Normalisierung verwenden — auch beim Bauen der Reply-To-Adresse,
sonst entsteht wieder ein Alias-Alias.

## Anhänge

Bilder und PDFs laufen in beide Richtungen: aus der Mail (Mailgun liefert `attachment-1..n`)
wie aus dem Web-Chat (Upload-Feld). Sie landen im KV, hängen als echte Datei an der Relay-Mail
und erscheinen im Verlauf als Vorschau. Erlaubt sind Bildformate und PDF bis 12 MB, maximal
fünf je Nachricht.

**Wer einen neuen Eingang baut, muss die Anhänge mitnehmen.** Genau das wurde beim ersten Bau
vergessen: der Text kam an, die zwei Fotos der Kundin verschwanden ersatzlos.

## Kontaktdaten werden geschwärzt

Telefonnummern, Mailadressen und fremde Links werden aus jeder Nachricht entfernt, bevor sie
weitergeht. Der Absender bekommt einen Hinweis, dass etwas ersetzt wurde, und Björn eine Kopie.
Wer am Chat arbeitet, darf diese Schwärzung nicht umgehen — sie ist der Grund, warum die
Vermittlung überhaupt über uns läuft.

## Preise im Chat

Nennt jemand im Chat einen Preis, der vom hinterlegten Angebot abweicht, schlägt eine Prüfung an
und informiert Björn. Häufigste Ursache ist kein Betrug, sondern ein ungepflegter
Saison-Zeitraum im Backend: die Suche rechnet dann mit dem Standardsatz statt der Hauptsaison,
und der Vermieter nennt im Chat den richtigen, höheren Preis. Das kostet uns Vertrauen beim
Kunden und Provisionsbasis. Erst die Preisliste prüfen, dann mit dem Vermieter reden.

## Wenn etwas fehlt: die Reihenfolge

1. Hat die **Mailgun-Route** gegriffen? (Routen auflisten, Alias mit dem Muster abgleichen.)
2. Steht die Nachricht in **`chat_partner`**? Wenn nein, hat der Worker sie nie gesehen.
3. Gibt es einen **`comm_log`**-Eintrag zum Vorgang? Er zeigt auch, was rausging.
4. Existiert eine **`chat_map`**-Zuordnung? Ohne sie wird nichts weitergeleitet, es kommt aber
   eine Meldung „Relay-Nachricht OHNE Zuordnung".
5. Erst dann Worker-Code oder Make-Szenario ansehen.

## Die Listenansicht fragt gesammelt, nicht je Zeile (21.08.2026)

`chatList` rief für **jede** der bis zu 40 Listenzeilen einzeln `GET /api/bookings/<id>` auf srv2
auf. Jeder dieser Aufrufe bootet dort ein komplettes Symfony — gemessen **112 Anfragen je Minute
rund um die Uhr** für immer dieselben rund 36 Vorgänge, also die halbe Grundlast der Box.

Seit dem 21.08. beantwortet **`/backend/cf-chatbulk.php`** alle IDs in einem Aufruf
(0,15 s für 7 IDs gegenüber 0,19 s für eine einzelne). Danach: **8 Anfragen je Minute.**

Der Endpoint entscheidet bewusst **nichts selbst**, sondern ruft dieselben Helfer wie der
Einzelabruf: `AccessHelper::userHasAccessToBooking` und `::cfContactIsMasked`. Damit kann die
Sichtbarkeit nicht auseinanderlaufen, auch nicht wenn die Maskierungsregeln wieder angepasst
werden. Ausgeliefert werden nur Flags (`v`, `full`) plus Firma, Ort und Kennzeichen —
**keine Kontaktdaten**. Deckel: 60 IDs je Aufruf, JWT-Pflicht (RS256 lokal gegen
`/home/gaz/rent/jwt/key.pub` geprüft).

Im Worker fällt **jede Zeile einzeln** auf den alten `bkFetch`-Weg zurück, wenn der Endpoint
nicht antwortet. Dann ist es wieder langsam, aber nie falsch. Rollback = Datei auf srv2 löschen.

**Wer eine neue Listen- oder Übersichtsansicht baut, fragt gesammelt.** Ein `Promise.all` über
40 Einzelabrufe sieht im Code harmlos aus und ist es nicht — parallel heißt nicht billig.

## Ein Cache, dessen Fehler niemand sieht, ist kein Cache (21.08.2026)

`bkFetch` cachte seine Antworten seit dem 12.08. in `caches.default` — und es hat **nie
funktioniert**. Zwei Gründe, beide lautlos:

1. Die Cache-API nimmt nur Schlüssel auf einem Hostnamen der **eigenen Zone** an. Der Schlüssel
   lautete `https://bk.cache.invalid/…` — diese Domain gehört uns nicht, der `put` schlug fehl.
2. Der Hauptaufrufer `/chat-list` läuft über **`cf-mailstatus.b-dunker.workers.dev`**, und
   **auf workers.dev ist die Cache-API wirkungslos**, egal welcher Schlüssel.

Weil jeder Fehler in einem leeren `catch (e) { }` landete, sah der Code monatelang nach „gefixt"
aus, während die Last unverändert weiterlief.

Daraus zwei Regeln:

- **Nach dem Einbau eines Caches messen, ob er greift** — Trefferquote oder schlicht die Last
  am Ziel. Ein Cache ohne Messung ist eine Behauptung.
- **`caches.default` nur auf einer eigenen Zonen-URL verwenden, nie auf workers.dev.** Wenn ein
  Endpunkt über workers.dev erreichbar sein muss, ist KV die richtige Ablage — oder man beseitigt
  wie oben gleich den Grund für die vielen Abfragen.

Ein Cache im Isolat (`BK_MEM`, Modul-globale `Map`) funktioniert überall und kostet nichts, wirkt
aber nur innerhalb eines Isolats: gemessen brachte er allein **112 → 84** Anfragen je Minute.
Erst der gesammelte Abruf brachte den Sprung auf 8.

## Verwandt

`camperfuchs-verfuegbarkeits-flow` (die Make-Szenarien, die den Chat füttern),
`camperfuchs-kontaktfreigabe` (wann Kontaktdaten freigegeben werden),
`camperfuchs-projekt` (Architektur drumherum).
