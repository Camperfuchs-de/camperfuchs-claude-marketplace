---
name: camperfuchs-agent-readiness
description: "Prüft und sichert die Agenten-/KI-Auffindbarkeit von camperfuchs.de (GEO/AEO) und triagiert die ganzen 'Agent-Discovery'-Standards nach ECHTEM Nutzen statt blind abzuhaken. Diese Skill IMMER nutzen, wenn jemand einen isitagentready.com-Report (oder ähnliche 'is your site agent ready'-Checks) reinwirft, oder fragt — explizit ('sind wir für KI-Agenten/ChatGPT/Perplexity auffindbar', 'Markdown for Agents prüfen', 'Link-Header', 'llms.txt prüfen', 'agent readiness', 'agentenbereit', 'AEO/GEO-Check', 'sollen wir OAuth/MCP-Server-Card/ACP/x402/DNS-AID/WebMCP/API-Catalog einbauen') wie implizit ('macht dieses Agenten-Protokoll für uns Sinn', 'warum ist Check X rot'). Liefert: Live-Verifikation per curl der wirklich wertvollen Dinge (Markdown for Agents, Link-Header→llms.txt, llms.txt) PLUS eine ehrliche Triage-Tabelle, welche Standards für einen Lead-Gen-Vermieter Mehrwert bringen und welche reiner Ballast bzw. schädliche Fake-Infrastruktur wären."
---

# Camperfuchs Agent-Readiness

Wiederverwendbarer Check, wie gut camperfuchs.de für KI-Agenten/Antwort-Maschinen (ChatGPT, Claude, Perplexity, Google AI) auffindbar ist — und eine ehrliche Bewertung der vielen neuen „Agent-Discovery"-Standards. Kernhaltung: **Nutzen vor Vollständigkeit.** Ein grüner Haken bei isitagentready.com ist kein Selbstzweck; ein leerer Stub ohne echtes Backend macht uns gegenüber Agenten KAPUTT, nicht besser.

## Wann diesen Skill nutzen

- Jemand wirft einen isitagentready.com-Report (o. ä.) rein und will wissen, was davon wir angehen sollen.
- Frage „sind wir für KI/Agenten auffindbar?", „Markdown for Agents / Link-Header / llms.txt prüfen", „lohnt sich Standard X (OAuth/MCP-Card/ACP/x402/…)".

## Architektur-Kontext

camperfuchs.de ist hinter **Cloudflare** (Pro) ein **Hybrid**: WordPress (Marketing) + Next.js-LP/Inventar-App. Agent-Discovery sitzt teils am **Edge** (Cloudflare, von uns steuerbar), teils bräuchte es ein echtes **Backend** (Auth-Server, MCP-Server, Commerce-API), das wir NICHT haben. Lead-Gen-Vermieter, kein Publisher und kein Instant-Checkout-Shop.

## Schritt 1 — Live-Check der wertvollen Dinge (curl)

```bash
# Markdown for Agents (Cloudflare AI Crawl Control) — erwartet: content-type: text/markdown + x-markdown-tokens
curl -sS -D - -o /dev/null -H "Accept: text/markdown" https://www.camperfuchs.de/ | grep -iE 'HTTP/|content-type|x-markdown-tokens|x-original-tokens'
# auch auf einer WP- UND einer Next.js-Seite gegenchecken (greift site-weit am Edge):
curl -sSL -D - -o /dev/null -H "Accept: text/markdown" https://www.camperfuchs.de/ihr-wohnmobil-ratgeber/faq/ | grep -i content-type
curl -sSL -D - -o /dev/null -H "Accept: text/markdown" https://www.camperfuchs.de/de/wohnmobil-mieten-guenstig/ | grep -i content-type

# Link-Header (RFC 8288) auf der Startseite — erwartet: rel="describedby" → llms.txt + rel="sitemap"
curl -sS -D - -o /dev/null https://www.camperfuchs.de/ | grep -i '^link'

# llms.txt vorhanden + aktuell?
curl -sS https://www.camperfuchs.de/llms.txt | head -40
```

Stand 07.06.2026 (verifiziert): Markdown for Agents ist AN und greift site-weit (WP + Next.js), ~85–90 % Token-Reduktion. Link-Header ist gesetzt (`<…/llms.txt>; rel="describedby"` + Sitemap). llms.txt existiert und ist gepflegt. Heißt: **die einzigen zwei wertvollen Punkte sind bereits erledigt.** Toggle für Markdown for Agents sitzt im Cloudflare-Dashboard unter AI Crawl Control.

## Schritt 2 — Ehrliche Triage der Standards

| Standard | Urteil | Warum |
|---|---|---|
| Markdown for Agents | ✅ TUN (ist live) | Cloudflare-Toggle, riesige Token-Ersparnis, direkter GEO/AEO-Nutzen |
| Link-Header → llms.txt (RFC 8288) | ✅ TUN (ist live) | Minimal, ehrlich, hilft Agenten-Discovery |
| llms.txt | ✅ TUN (ist live) | Etablierter Standard, billig, sinnvoll |
| OAuth/OIDC-Discovery, OAuth-Protected-Resource, auth.md | ❌ LASSEN | Brauchen einen echten Auth-Server für Agenten. Haben wir nicht. Stub → Agent versucht Login → scheitert → Seite wirkt kaputt |
| MCP-Server-Card | ❌ LASSEN | Nur wahr, wenn wir einen MCP-Server betreiben. Tun wir nicht |
| API-Catalog (RFC 9727) | ❌ LASSEN | Braucht öffentliche OpenAPI-Spec. Unsere Buchungs-API ist intern |
| DNS-AID | ❌ LASSEN | Nur ein IETF-Entwurf; will SVCB + DNSSEC und zeigt auf Agenten-Endpunkte, die es nicht gibt |
| Agent-Skills-Index, WebMCP | ❌ LASSEN | Bleeding-edge; nichts zu listen / großer Bau für hypothetischen Nutzen |
| x402 (Krypto-HTTP-Zahlung) | ❌ LASSEN | Irrelevant für Anfrage-/Lead-Modell |
| ACP (Agenten-Checkout) | ❌ LASSEN | Wir sind Lead-/Anfrage-basiert, kein Instant-Checkout. Großer Bau |

**Regel:** Einen `.well-known`-Endpunkt nur veröffentlichen, wenn das dahinterliegende Ding ECHT existiert. Sonst nicht.

## Gotchas (teuer gelernt)

- **isitagentready.com meldet oft „Could not check … The operation was aborted"** — das ist ein TIMEOUT auf Seiten des Checkers, KEIN Loch bei uns. Per curl gegenchecken (die Header sind nachweislich da). Nicht hinterherjagen.
- **Stubs sind schlimmer als Nichts:** ein `.well-known`-Dokument, das auf 404-Endpunkte zeigt, macht den Check NICHT grün (Endpunkte 404en) und lässt die Seite gegenüber Agenten defekt wirken.
- Markdown for Agents setzt `vary: accept`; koexistiert sauber mit APO-Cache (von Cloudflare so gebaut) — bisher kein Cache-Konflikt beobachtet.

## Output

Kurzer Report: zuerst die Live-Verifikation (was ist grün), dann die Triage (was lohnt sich / was bewusst lassen), nach Impact sortiert. Keine Fake-Endpunkte vorschlagen.

Siehe auch [[project-camperfuchs-ai-strategy]].
