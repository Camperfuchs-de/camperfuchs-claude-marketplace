---
name: camperfuchs-sammelanfrage
description: >
  Bauen, Aendern und Debuggen der Camperfuchs Sammelanfrage + Merkzettel — mehrere Fahrzeuge in
  einem Zug unverbindlich anfragen, seit „Weg 2" mit eigenem Reisezeitraum + Zubehoer JE Fahrzeug.
  IMMER nutzen, wenn Sammelanfrage/Merkzettel Thema sind — explizit („Sammelanfrage aendern",
  „Merkzettel", „Fahrzeuge gemerkt", „Zeitraum je Fahrzeug", „merkMode", „Zur Sammelanfrage
  uebernehmen", „bookings/group", „fare-Endpoint") wie implizit („Kunde muss das Datum nochmal
  eingeben", „Preis am gemerkten Fahrzeug stimmt nicht", „Rueckweg von der Detailseite geht
  nicht"). Enthaelt System-Landkarte (MerkzettelContext, sammelanfrage.tsx, BookingCalculator
  merkMode, Detailseite merk/merkLoc, Backend fare+group), Datenmodell, Endpoints und die teuer
  gelernten Fallen: update() ist auf article+articleLocation gekeyt (falsches merkLoc schreibt
  still nichts), extras speichert NAMEN statt Indizes, /sammelanfrage per Direkt-URL haengt
  (separate Routing-Luecke). NICHT fuer den Verfuegbarkeits-Flow oder die Deploy-Kette.
metadata:
  type: skill
  scope: camperfuchs-rentanda
---

# Camperfuchs Sammelanfrage & Merkzettel

Der Kunde merkt sich in der Suche mehrere Fahrzeuge und fragt sie auf `/sammelanfrage` in einem
Zug unverbindlich an. Seit **„Weg 2"** (PR #1214, live prod 08.07.2026) hat **jedes gemerkte
Fahrzeug seinen eigenen Reisezeitraum + Zubehoer** — es gibt kein globales Pflicht-Datum mehr,
das der Kunde neu eingeben muss.

## System-Landkarte

| Was | Datei |
| --- | --- |
| Merkzettel-State (localStorage) | `frontend/app/modules/merkzettel/MerkzettelContext.tsx` |
| Sammelanfrage-Seite | `frontend/pages/sammelanfrage.tsx` |
| Merkzettel-Pille („N Fahrzeuge gemerkt · Alle anfragen") | `frontend/app/components/Merkzettel/MerkzettelBar.tsx` |
| „Zur Sammelanfrage merken" auf Suchkarten | `frontend/app/components/Tools/QueryResultCard.tsx` |
| Buchungsrechner + Rueckweg-Button | `frontend/app/components/Tools/BookingCalculator.tsx` |
| Detailseite (setzt `merkMode`) | `frontend/pages/wohnmobil-mieten/[location]/[subtype]/[slug]/index.tsx` |
| Backend Preis/Zubehoer + Gruppen-Anfrage | `backend/.../articles/controller/ArticleController.java`, `.../articles/service/ArticleService.java` |

**PR-Historie:** #1191 (Backend group) → #1194 (Frontend) → #1200 (Preise/Zeitraum je Fahrzeug)
→ **#1214 (Weg 2, Zubehoer je Fahrzeug + Rueckweg)**.

## Datenmodell

```ts
interface MerkzettelItem {
  article: string          // Artikel-ID
  articleLocation: string  // Station — Teil des Schluessels!
  title: string
  thumb?: string; uri?: string; location?: string
  from?: string; to?: string      // eigener Zeitraum je Fahrzeug (Weg 2)
  extras?: string[]               // Zubehoer als NAMEN, nicht Indizes
  totalPrice?: number; discountedTotalPrice?: number
}
```

- Context: `{ items, hydrated, has, toggle, update, remove, clear }`
- `update(article, articleLocation, patch)` patcht ein bestehendes Item gezielt.
- Persistenz: `localStorage` unter **`cf_merkzettel_v1`**; `keyOf = \`${article}__${articleLocation}\``.
- `hydrated` verhindert SSR-Mismatch — vor `hydrated` nichts rendern, sonst Flackern/Hydration-Error.

## Der Weg-2-Flow

1. `/sammelanfrage` listet je Fahrzeug eine Zeile mit eigenem Zeitraum, Preis, Zubehoer.
2. „aendern" / „Zeitraum waehlen" verlinkt auf die Detailseite:
   `{item.uri}?from=…&to=…&merk=1&merkLoc={articleLocation}`
3. Detailseite: `merkActive = query.merk === '1' || 'true'` →
   `merkMode = { articleLocation: String(query.merkLoc || article?.relevantStationId || '') }`
   Wird an **beide** `BookingCalculator`-Instanzen (Desktop **und** Mobile) durchgereicht.
4. Im Rechner erscheint bei `merkMode` der Hinweis + Button **„Zur Sammelanfrage uebernehmen"**:
   schreibt `{ from, to, extras: [...selectedAddons] }` per `updateMerk(...)`, feuert
   `captureEvent('sammelanfrage_fahrzeug_uebernommen')` und geht per `router.push('/sammelanfrage')`
   zurueck (kein Hard-Reload, damit der Merkzettel-State lebt).
5. Optionaler Komfort: Schnellsetzer „± Fuer alle Fahrzeuge denselben Zeitraum setzen"
   (`applyBulk` → `update()` auf allen Items). Pro Fahrzeug bleibt er ueberschreibbar.

## Endpoints

**Preis + Verfuegbarkeit + Zubehoer je Fahrzeug**
`GET /api/V1/articles/{article}/{articleLocation}/fare?from=YYYY-MM-DD&to=YYYY-MM-DD`
→ `totalPrice`, `discountedTotalPrice`, `availableInWindow`, `availableSlotFrom`,
`availableSlotTo`, `additions[{ index, name, rate, daily, mandatory }]`

Die Sammelanfrage laedt das je Item neu, sobald sich dessen Zeitraum aendert (Trigger ist die
Signatur `datesSig` aus allen `article:from:to`).

**Absenden**
`POST /api/V1/bookings/group` mit
```json
{ "requests": [ { "type": "REQUEST", "booking": {
  "additions": { "<index>": true }, "article": "…", "articleLocation": "…",
  "from": "…", "to": "…", "firstname": "…", "email": "…", "acceptAgb": true } } ] }
```
Antwort: `{ created: [...], failed: [...] }` → `SuccessBlock` zeigt beides getrennt an.
Danach `captureEvent('sammelanfrage_abgeschickt')`, `gtmPush({event:'cf_anfrage_gesendet'})`, `clear()`.

**Nur diese Fahrzeuge gehen raus:** gueltiger Zeitraum **und** `fare.available !== false`.
Fuer den Rest zeigt die Seite die Hinweise `anyOhneDatum` / `anyBelegt`.

## Teuer gelernte Fallen

- **`update()` ist auf `article` + `articleLocation` gekeyt.** Ein Detailseiten-Aufruf mit
  falschem oder erfundenem `merkLoc` (z.B. `?merk=1&merkLoc=1` zum Testen) findet kein Item →
  **stiller No-op**, der Klick wirkt folgenlos. Beim Testen IMMER die echte `articleLocation` des
  gemerkten Fahrzeugs nehmen, sonst diagnostiziert man faelschlich „Rueckweg kaputt".
- **`extras` speichert NAMEN, die Checkboxen arbeiten mit `index`.** `sammelanfrage.tsx` mappt
  Namen → Indizes zurueck, sobald die `fare`-`additions` geladen sind (`addInitSig` verhindert,
  dass inline gesetzte Haken ueberschrieben werden). Wer auf Indizes umstellt, muss beide Seiten
  anfassen.
- **`/sammelanfrage` per Direkt-URL haengt / 404t.** Bekannte, vorbestehende Routing-Luecke
  (`/sammelanfrage`, `/merkzettel`, `/group` sind nicht an Next geroutet) — **nicht** Weg 2. Der
  In-App-Weg (Suche → merken → „Alle anfragen") funktioniert. Beim Verifizieren immer in-app
  navigieren, sonst Fehlalarm.
- **Zwei `BookingCalculator`-Instanzen** auf der Detailseite (Desktop + Mobile). Aenderungen
  gehoeren in die Komponente, nicht in eine der beiden Einbindungen.
- **`noindex`:** `/sammelanfrage` traegt bewusst `robots: noindex,follow`.

## Verifikation (Browser)

Fahrzeug in der Suche merken (mit Datum) → Pille „Alle anfragen" → `/sammelanfrage` → „aendern"
→ Detailseite → Zeitraum/Zubehoer aendern → „Zur Sammelanfrage uebernehmen" → zurueck: Zeitraum,
Preis und Zubehoer des Fahrzeugs muessen uebernommen sein, ohne Neu-Eingabe.

Fallen dabei (09.07. gelernt):
- **Screenshots timen auf den Fahrzeug-Detailseiten aus** (CDP 30 s — schwere Galerie + Carousel
  + Chat-Widget). Auf **`get_page_text`** ausweichen; `/sammelanfrage` selbst ist leicht genug.
- **`read_page filter:interactive` verschluckt Elemente**, die `get_page_text` zeigt — Abwesenheit
  dort ist KEIN Beleg fuer „nicht live".
- Der Rechner ist eine **Sticky-Sidebar**: Seiten-Scroll bringt den Button am Kartenende nicht ins
  Bild → `read_page` → ref → `scroll_to {ref}` → per ref klicken.
- **Mobile-Optik laesst sich nicht simulieren** (`resize_window` aendert `innerWidth` nicht) →
  Bjoern schaut auf dem Handy. Nie ein Desktop-Layout als „mobil geprueft" ausgeben.

## Stand

Weg 2 ist **live auf prod seit 08.07.2026** (Merge `672680b5`, def13-Build) und **vollstaendig
abgenommen**: Desktop verifiziert (je Fahrzeug eigener Zeitraum + Preis + Zubehoer, Rueckweg-Button
auf der Detailseite), **Mobile-Optik von Bjoern am Handy geprueft (14.07.) — sitzt**.
Offen bleibt nur die `/sammelanfrage`-Direkt-URL-Routing-Luecke (eigenes Ticket, nicht Weg 2).
