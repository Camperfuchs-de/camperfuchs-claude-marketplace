---
name: cf-tafel
description: "Pflicht-Arbeitsweise fuer parallele Claude-Sessions bei Camperfuchs/Rentanda ueber die zentrale Tafel https://tafel.camperfuchs.de - anmelden (start), Ressourcen sperren (lock), auf Bjoern Wartendes eintragen (wartet), abmelden (ende). IMMER nutzen, sobald an irgendetwas fuer Camperfuchs gearbeitet wird - egal ob Code, Server, Make, WordPress, SEO oder Buchhaltung - auch wenn Bjoern es nicht ausdruecklich sagt. Explizit ('Tafel', 'cf start', 'wer arbeitet gerade', 'Sperre setzen', 'was wartet auf mich') wie implizit (Session-Anfang, vor einem Deploy, vor Aenderungen an srv2/Make/WordPress/Workern, wenn eine Entscheidung von Bjoern fehlt). Mehrere Sessions laufen parallel ueber drei Accounts und sehen sich gegenseitig nicht - die Tafel ist der einzige gemeinsame Ort. Enthaelt die curl-Rezepte fuer Sessions ohne Zugriff auf F: sowie die Regeln (Ablauf ist Pflicht, BELEGT heisst Finger weg, Fertig heisst raus)."
---

# cf-tafel — Zusammenarbeit paralleler Sessions

Bjoern fuehrt mehrere Claude-Sessions gleichzeitig (Accounts: A = b.dunker@, B = office@,
C = info@, oft mehrere Fenster je Account). Jede Session sieht nur sich selbst. Am 18.08.2026
haben zwei Accounts denselben Fix doppelt gebaut; am 21.08. hat ein Deploy den Patch einer
anderen Session lautlos ueberschrieben. **Die Tafel ist der einzige gemeinsame Ort.**

**Ansehen (offen, ohne Schluessel):** https://tafel.camperfuchs.de
Zeigt: Braucht dich (wartet auf Bjoern) → Achtung → Aktive Sitzungen → Gesperrt →
Heute abgeschlossen → Ueberwachte Systeme → Offene Faeden. Aktualisiert sich jede Minute.

## Der Pflicht-Ablauf

1. **Session-Anfang: anmelden.** Der Server vergibt das Kuerzel (A1, B2, ...). Kuerzel merken
   und an jeden weiteren Aufruf haengen.
2. **Vor JEDER Aenderung an Code, Server, Make oder WordPress: sperren.** Antwort ist
   `ok` oder `belegt`. **BELEGT heisst Finger weg** — auch wenn die eigene Aenderung
   "sowieso dieselbe" waere. Erst klaeren, wer die Sperre haelt.
3. **Wenn eine Entscheidung von Bjoern fehlt: sofort eintragen** (`/wartet`), nicht im Chat
   sterben lassen. Die Frage so formulieren, dass er sie OHNE den Chat beantworten kann.
4. **Session-Ende: abmelden.** Loest alle eigenen Sperren, schreibt ins Journal.
5. **Zwischendurch** (bei langen Sessions alle paar Stunden): Zustand melden (`/beat`) mit
   Thema-Stand und Token-Restbudget — die Tafel warnt Bjoern, wenn ein Budget knapp wird.

## Zugriff

**Schluessel:** liegt in `C:\Users\bjoer\Documents\Claude\Projects\Camperfuchs Tech & Produkt\.secrets\tafel-key.txt`
(per Desktop Commander lesen). Er steht ABSICHTLICH nicht in dieser Skill. Lesen geht ohne
Schluessel, jedes Schreiben braucht ihn als Header `x-tafel-key`.

**Mit PC-Zugriff (Desktop Commander, nur Account A eingerichtet):** `F:\dev\cf.cmd`
mit den Befehlen `start "<thema>" -Account B`, `lock <was> <dauer> "<grund>" -Session B1`,
`wartet "<thema>" "<frage>" <art>`, `erledigt <nr> "<antwort>"`, `ende <kuerzel> -Ja`, `lage`.

**Ohne PC-Zugriff (Sandbox-Bash — funktioniert in JEDER Session):**

```bash
K=<schluessel aus tafel-key.txt>
U=https://tafel.camperfuchs.de

# Lage (offen)
curl -s "$U/lage?json=1"

# Anmelden - Kuerzel kommt vom Server. account: A|B|C je nach eigenem Account.
curl -s -X POST "$U/start" -H "x-tafel-key: $K" -H 'content-type: application/json' \
  -d '{"thema":"<kurz was du tust>","account":"B"}'

# Sperren - dauer ist PFLICHT (30m|4h|2d). Antwort ok:true ODER belegt:true (immer HTTP 200).
curl -s -X POST "$U/lock" -H "x-tafel-key: $K" -H 'content-type: application/json' \
  -d '{"ressource":"srv2:cf-frist.php","kuerzel":"B1","dauer":"2h","grund":"<warum>"}'

# Auf Bjoern Wartendes eintragen. art: handgriff|freigabe|rueckfrage|entscheidung.
# blockiert = was dadurch stillsteht (macht den Preis sichtbar).
curl -s -X POST "$U/wartet" -H "x-tafel-key: $K" -H 'content-type: application/json' \
  -d '{"thema":"<kurz>","frage":"<ohne Chat beantwortbar>","art":"entscheidung","wer":"B1","blockiert":"<was liegt still>"}'

# Bjoerns Entscheidung uebernehmen (schreibt sie ins Journal, wo die wartende Session sie findet)
curl -s -X POST "$U/wartet" -H "x-tafel-key: $K" -H 'content-type: application/json' \
  -d '{"erledigt":<nr>,"antwort":"<was entschieden wurde>","wer":"B1"}'

# Zwischenstand + Budget melden (tokens_rest = eigener total_tokens-Zaehler, tokens_max = 15000000)
curl -s -X POST "$U/beat" -H "x-tafel-key: $K" -H 'content-type: application/json' \
  -d '{"kuerzel":"B1","stand":"<eine Zeile>","modell":"<modellname>","tokens_rest":<zahl>,"tokens_max":15000000}'

# Offenen Rest notieren, der keine Session mehr hat
curl -s -X POST "$U/faden" -H "x-tafel-key: $K" -H 'content-type: application/json' \
  -d '{"thema":"<kurz>","was_fehlt":"<was noch zu tun ist>","quelle":"<datum>"}'

# Sperre freigeben / verlaengern: /unlock {"ressource":...} bzw. neu /lock mit gleicher Ressource

# Abmelden - loest alle eigenen Sperren
curl -s -X POST "$U/ende" -H "x-tafel-key: $K" -H 'content-type: application/json' \
  -d '{"kuerzel":"B1","notiz":"<eine Zeile was erledigt ist>"}'
```

## Feste Sperr-Namen (nicht erfinden)

`deploy-kette` (das Monorepo main→staging→prod — EIN Build-Agent, nie parallel!) ·
`srv2:<datei>` · `srv2:cron` · `worker:<name>` · `make:<id>` · `wp:snippets` · `wp:seiten` ·
`repo:<pfad>` · `cf-marketplace` (das geteilte Plugin-Repo)

## Die Regeln (teuer gelernt)

- **Ablauf ist Pflicht.** Eine Sperre ohne Ende blockierte einmal 6 Tage lang den
  Live-Anfrage-Eingang, ohne dass jemand daran arbeitete. Abgelaufene Sperren loescht der
  Server selbst.
- **Fragen statt lesen.** Eine Session handelte nach einer Sperr-Datei, die eine halbe Stunde
  veraltet war. Die Tafel antwortet im Moment der Aktion.
- **Fertig heisst raus.** `ende` aufrufen, nicht "erledigt" irgendwo hinschreiben und die
  Anmeldung stehen lassen.
- **Fingerabdruecke ernst nehmen.** Die Tafel ueberwacht Worker, Make-Szenarien und
  WordPress-Snippets per Hash (`/abdruck`). Meldet sie GEAENDERT, hat eine andere Session dort
  gearbeitet — erst klaeren, nie blind uebernehmen. Auf srv2 gilt zusaetzlich: vor jedem
  Deploy `bash /usr/local/cf/cf-drift.sh --kurz`, nach eigener Arbeit
  `cf-commit.sh "was und warum" <kuerzel> <datei...>`.
- **Vor jedem Vorschlag an Bjoern:** erst die Tafel (und in Cowork `list_sessions`) pruefen,
  ob das Thema schon woanders laeuft. Nichts vorschlagen, was gerade eine andere Session baut.
