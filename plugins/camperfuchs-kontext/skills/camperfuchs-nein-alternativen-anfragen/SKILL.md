---
name: camperfuchs-nein-alternativen-anfragen
description: >
  Feature „Bei NEIN konkrete Alternativen beim jeweiligen Vermieter anfragen": Sagt ein Vermieter
  zu einer Mietanfrage NEIN, oeffnet Bjoern aus der NEIN-Info-Mail per Button eine Picker-Seite mit
  den tatsaechlich freien Fahrzeugen im Zeitraum/Umkreis (Filter Personen/Betten, Bauart, Preis,
  Haustiere, Umkreis) und schickt pro Fahrzeug mit einem Klick eine Verfuegbarkeits-Anfrage an
  genau diesen Alt-Vermieter. IMMER nutzen bei „Alternativen anfragen"-Button/-Seite, Picker zeigt
  keine oder falsche Fahrzeuge, Filter aendern, „Anfrage geht nicht an den Alt-Vermieter raus",
  landlord-contact-Endpoint, Szenario 6559455, Hook m5jc…, Personenzahl-Filter (Erwachsene+Kinder).
  Enthaelt die System-Landkarte (Backend-Endpoint landlord-contact key-gated, Make 6559455 mit
  Picker-Route alt=1 + Send-Route send_alt=1, Modul-5-Button in 6030776, Personen-Parser in
  5482694) und die teuer gelernten Fallen. NICHT fuer den JA/NEIN/Rueckfrage-Grundflow selbst
  (→ camperfuchs-verfuegbarkeits-flow) oder die 5482694-Grundlogik.
---

# Camperfuchs: NEIN-Alternativen beim jeweiligen Vermieter anfragen

Ziel: Sagt ein Vermieter zu einer Mietanfrage NEIN, soll Björn dem Mieter schnell **echte freie Alternativen** anbieten können — und zwar so, dass jeder Alt-Vermieter selbst bestätigt (kein Versprechen, dass ein Fahrzeug frei ist; "verfügbar" in der Suche ist nur Kalender-Ebene). Live seit 14.07.2026.

## Ablauf (End-to-End)

1. **Anfrage kommt rein** → Szenario **5482694** ("Integration Gmail") parst die Anfrage-Mail und schreibt einen Tracking-Record in Datastore **131528** (Key `vermieter|betreff`). NEU: parst auch **Personenzahl** (s.u.) → Feld `personen`.
2. **Vermieter klickt NEIN** → Szenario **6030776** (Hook `tu2xumx8rhjynvul6l2stjxq7r5mcc55`), Confirm-Route, **Modul 5** = Info-Mail an Björn ("Vermieter NICHT verfügbar (NEIN): …"). Deren Button **"Freie Alternativen anfragen"** zeigt auf den **Picker** (Hook m5jc…) mit allen nötigen Params.
3. **Björn klickt den Button** → Picker-Seite (Szenario **6559455**, Route `alt=1`) lädt per JS die freien Fahrzeuge der Such-API und zeigt sie mit Filtern.
4. **Björn klickt "Bei diesem Vermieter anfragen"** → Route `send_alt=1` desselben Szenarios: löst Vermieter-Mail via Backend-Endpoint auf, verschickt die Verfügbarkeits-Mail (JA/NEIN/Rückfrage) an den Alt-Vermieter, schreibt Tracking (131528).
5. **Alt-Vermieter antwortet JA/NEIN** → Buttons der Alt-Mail zeigen auf **tu2/6030776** → läuft in den bestehenden Flow + Tracking zurück (Björn-Info + Mieter-Entwurf).

## System-Landkarte (IDs)

- **Backend-Endpoint:** `GET https://www.camperfuchs.de/api/V1/articles/{articleId}/landlord-contact?key=…` → `{email, companyName, firstName, lastName, title}`. Key-gated über `environment.getProperty("cf.landlord-contact-key", <default-im-code>)`, env `CF_LANDLORD_CONTACT_KEY` überschreibt (Spring relaxed-binding). `/V1/articles/**` ist permitAll → Gate liegt im Code (ArticleService.getLandlordContact). Reverse zu findArticlesByLandlordEmail: `getArticleById` + `getArticleLocationByArticlId` (VISIBLE-Variante! NICHT die *ForSale*-Variante — die filtert !visible und liefert bei Miet-Fahrzeugen leer). Deploy = Monorepo-PR → main→staging→prod (Prod-Environment-Gate selbst approven, s. Memory azure-env-approvals). ⚠️ Key liegt aktuell als Default im Code (privates Repo, v1-Kompromiss) → später auf echtes env-Secret rotieren.
- **Make-Szenario 6559455** "NEIN-Alternativen anfragen", Team 345711, Hook **3390986** = `https://hook.eu1.make.com/m5jcmvmvw2dkfoyv6vp9q5i3fla2k31a`. Module: `#1` CustomWebHook, `#10` BasicRouter → Route A `#20` WebhookRespond = **Picker-Seite** (Filter `alt=1`), Route B `#30` http landlord-contact → `#31` google-email Verfügbarkeits-Mail → `#32` datastore AddRecord (131528) → `#34` WebhookRespond Danke (Filter `send_alt=1`).
- **Make-Szenario 6030776** Modul **5** = NEIN-Info-Mail an Björn; Button-href baut die Picker-URL (s. Params unten). Modul **20** = Vermieter-Picker (eigene NEIN-Alternative des absagenden Vermieters) mit Datumsfeldern für "Alternativer Zeitraum".
- **Make-Szenario 5482694** Modul `#7` Haupt-Parser; NEU `#18` Regex Erwachsene, `#19` Regex Kinder; Modul `#13` AddRecord schreibt `personen`.
- **Datastore 131528** "Verfügbarkeits-Tracking", Key `vermieter|betreff`. Relevante Felder: ort, zeitraum ("DD-MM-YYYY bis DD-MM-YYYY"), kunde, mieter, fahrzeug, betreff, status, **personen** (=Erwachsene+Kinder).

## Picker-URL (Modul-5-Button → m5jc-Hook, Route alt=1)

`…/m5jc…?alt=1&from=<YYYY-MM-DD>&to=<YYYY-MM-DD>&address=<ort>&lat=<>&lon=<>&mieter=<>&vorname=<>&betreff=<>&personen=<N>`
- `from/to` = geparst aus `40.zeitraum` (split "bis", parseDate DD-MM-YYYY → YYYY-MM-DD).
- `lat/lon/address` = Nominatim-Geocode von `40.ort` (Modul 44), Fallback by-landlord-Location (Modul 42).
- `personen` = `encodeURL(40.personen)` (leer bei Alt-Records → kein Filter).

## Picker-Seite (6559455 Modul 20, client-JS)

Liest URL-Params, fetcht `GET /api/V1/articles?from&to&lat&lon&distance=<dyn>&onlyAvailable=true&page=0&size=100` **+ `&minBeds=<personen>`** wenn personen>0. Danach **client-seitige** Filter auf der geladenen Liste (sofort, kein Reload): Bauart-Chips (subType), max. Preis (totalPrice), Haustiere (petsAllowed). **Umkreis**-Dropdown (50/100/120/200/250) ändert `distance` → Reload. Jede Karte hat "Bei diesem Vermieter anfragen" → `m5jc…?send_alt=1&article_id&title&url&mieter&vorname&betreff&von&bis&ort`.

## Send-Route (6559455 send_alt=1)

http #30 GET landlord-contact (→ `30.data.email`) → google-email #31 `to = {{if(1.test; "b.dunker@camperfuchs.de"; 30.data.email)}}` (**Test-Schalter!**) → AddRecord #32 (Key `{{30.data.email}}|{{1.betreff}}`) → Danke #34. Die JA/NEIN/Rückfrage-Buttons der Alt-Mail zeigen bewusst auf **tu2/6030776** mit `vermieter={{30.data.email}}` → Antwort läuft in den Bestandsflow.

## Gotchas (teuer gelernt)

- **Kapazitäts-Filter der Such-API = NUR `minBeds=N`.** `persons/seats/beds/maxPersons/personen` filtern NICHT (bleiben wirkungslos). Beispiel: Raesfeld 16-30.10 → 92 Treffer, `minBeds=5` → 36 (alle ≥5 Betten).
- **Personenzahl steht im Bemerkungsfeld** der Anfrage, Format `Anzahl Erwachsene: N` / `Anzahl Kinder: M`. Parse mit zwei SEPARATEN Regex-Modulen (continueWhenNoRes), NIE den Haupt-Regex #7 anfassen (bricht sonst den ganzen Parse → leere Vermieter-Mail). personen = `if(18.erw; parseNumber(18.erw); 0) + if(19.kin; parseNumber(19.kin); 0)`. Greift nur für NEUE Anfragen (Alt-Records ohne personen → leer → kein Filter).
- **landlord-contact:** Miet-Variante (`getArticleLocationByArticlId`, visible) nutzen — die *ForSale*-Variante liefert bei Miet-Fahrzeugen leer (Fehler "ArticleLocation … not found").
- **Test ohne echte Partner:** `send_alt=1&test=1&article_id=…` → Mail geht an b.dunker@, `30.data.email` wird trotzdem aufgelöst (in Buttons/Record sichtbar). Ohne test=1 geht die Mail an den ECHTEN Alt-Vermieter.
- **6030776 per scenarios_update:** Der ORIGINAL-Blueprint (ohne eingefügte Zusatzrouten) ist ~41KB → mehrzeilig (`json.dumps indent=1`) les-/emittierbar. Vor jedem Update die 9 Streak- + 7 Bild-Tokens der Gmail-Signaturen (Modul 10/22) sichern und NACH dem Update gegenprüfen (opake Token-Abschneide-Falle). Blueprint {name,flow,metadata} — top-level scheduling/interface strippen.
- **subType-Werte:** `alkoven` (Alkoven), `kasten` (Kastenwagen), `teil` (Teilintegriert), `voll` (Vollintegriert), `wagen` (Wohnwagen). **Getriebe/Automatik gibt es NICHT** in der Such-API (kein Feld) → nicht filterbar.

## Test-Rezept (nur b.dunker, headless per curl)

1. Record seeden (data-store-records_create, DS 131528, Key `b.dunker@camperfuchs.de|DEMO`, mit ort/zeitraum/personen).
2. NEIN auslösen: `curl -G "…/tu2…" --data-urlencode confirm=1 --data-urlencode aktion=nein --data-urlencode vermieter=b.dunker@camperfuchs.de --data-urlencode betreff=DEMO --data-urlencode mieter=b.dunker@camperfuchs.de --data-urlencode vorname=Test` → NEIN-Mail an Björn; Button-URL prüfen (personen dran?).
3. Picker: `curl -G "…/m5jc…" --data-urlencode alt=1 --data-urlencode from=… --data-urlencode to=… --data-urlencode lat=… --data-urlencode lon=… --data-urlencode personen=5` → HTML mit Filterleiste (typeChips/fMax/fPets/fDist).
4. Send: `…/m5jc…?send_alt=1&test=1&article_id=<echte-id>&title=…&mieter=b.dunker@…&…` → Danke-Seite + Testmail an Björn + Tracking-Record.
5. Aufräumen: DS-131528- + DS-131793-Testrecords löschen.

Details/Deploy-Mechanik: Skill `camperfuchs-vermieter-verfuegbarkeit-buttons` (6030776) und Memory `nein-alternativen-anfragen-feature`.
