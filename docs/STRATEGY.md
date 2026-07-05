# Strategie produktu (pracovní název: Pohoda Analytics)

## Teze

V ČR/SK je ~300 tis. instalací IS POHODA. Naprostá většina majitelů firem z ní
neumí dostat odpověď na otázky "jak nám jde byznys, kdo mi dluží, co se děje se
skladem" bez účetní nebo Excelu. FameDash dokázal, že se za to platí 2–4 tis.
Kč/měs. My máme z Vitar Sport dashboardu ověřené, které přehledy majitel firmy
skutečně používá denně.

## Pozicování

**"Rozumíte svojí firmě za 10 minut. Bez konzultanta, bez Excelu."**

- FameDash prodává *platformu a služby* (konzultace, konfigurace, školení).
- My prodáváme *hotový produkt*: self-service onboarding, hotové přehledy,
  moderní UX, AI vrstva. Product-led growth místo sales-led.

Diferenciace v pořadí důležitosti:
1. **Onboarding bez lidí** — zdarma vyzkoušet na vlastních datech (XML export
   přetáhnout do prohlížeče, zpracování client-side = žádné GDPR riziko v trialu).
2. **AI přehledy** — měsíční shrnutí lidskou řečí, upozornění na anomálie
   (propad marže, rostoucí pohledávky u konkrétního odběratele), dotazy přirozeným jazykem.
3. **Cena** — vstup výrazně pod 1 890 Kč.
4. **Design** — reporty, které jednatel rád otevře na mobilu a pošle bance.

## Jméno a ochranná známka — DŮLEŽITÉ

"POHODA" je ochranná známka STORMWARE s.r.o. Název **nesmí** vypadat, že jde
o produkt Stormware ("Pohoda Analytics" je rizikové jako primární brand).
Doporučení:
- zvolit vlastní brand (návrhy: **Přehledno**, **Bystro**, **Kormidlo**, **Maják**)
  a Pohodu používat jen popisně: "analytika pro IS POHODA" (nominative fair use),
- doménu bez slova "pohoda",
- prověřit rejstřík ÚPV před registrací domény,
- zvážit partnerský program Stormware (POHODA Plus) — legitimizuje napojení.

Repo `pohodaanalytics` je jen pracovní název, brand rozhodneme před spuštěním webu.

## Cílové segmenty

1. **Majitel malé/střední firmy s Pohodou** (5–50 zaměstnanců, e-shop/velkoobchod/služby)
   — platí on, používá on. Primární segment.
2. **Účetní kanceláře** — jeden účet, N klientů (účetních jednotek), reporting
   klientům jako přidaná služba. Sekundární, ale nejlepší LTV (FameDash to ví —
   tarifikace po ú.j.).
3. Later: franšízy/řetězce s více provozovnami.

## Cenový model (návrh k validaci)

| Tarif | Cena/měs. bez DPH | Obsah |
|---|---|---|
| **FREE / Trial** | 0 | ruční XML import v prohlížeči, 1 uživatel, bez historie |
| **SOLO** | 690 Kč | konektor (1 ú.j.), 2 uživatelé, všechny přehledy, e-mail digest |
| **FIRMA** | 1 490 Kč | 3 ú.j., 10 uživatelů, AI shrnutí + anomálie, PDF reporty, API |
| **KANCELÁŘ** | 2 990 Kč | 10 ú.j. (+250 Kč/další), white-label reporty pro klienty |

Roční platba −20 %. Cíl: 100 platících zákazníků do 12 měsíců od launche
(~100–150 tis. Kč MRR), break-even provozních nákladů cca při 15 zákaznících.

## Go-to-market

1. **Free nástroj jako magnet:** "Zdarma analýza vašich faktur z Pohody" —
   drag & drop XML, výsledek hned, data neopouští prohlížeč. Sdílitelné, SEO-friendly.
2. **Obsah/SEO:** "jak dostat data z Pohody", "reporting v Pohodě", "Pohoda export
   XML návod" — long-tail dotazy s nulovou konkurencí.
3. **Účetní kanceláře:** direct outreach + provize 20 % z prvního roku.
4. **Komunity:** FB skupiny účetních, podnikatelské skupiny, srovnávače SW.
5. **Případové studie** od prvních pilotů (nabídnout 6 měsíců zdarma za studii).

## Fáze a milníky

- **F0 (hotovo):** demo dashboard s fiktivními daty + XML import v prohlížeči.
- **F1 (validace, 2–4 týdny):** landing + demo online, 10 rozhovorů s majiteli
  firem s Pohodou, 3 piloti na vlastních XML exportech. Rozhodnutí go/no-go.
- **F2 (MVP SaaS, 6–8 týdnů):** účty, workspace, uložená data (Postgres),
  konektor v1 (naplánovaný XML export → push), Stripe/GoPay billing.
- **F3 (růst):** mServer live sync, AI vrstva, účetní kanceláře, SK lokalizace.

## Rizika

- **Stormware známka/API podmínky** — vyřešit brand + právní konzultace (F1).
- **FameDash má náskok a služby** — nekonkurovat službami, ale produktem a cenou.
- **Přístup k datům u MDB verzí Pohody** — XML export funguje všude; mServer jen
  E1/SQL? → ověřit v F1 (technická validace na 3 pilotech s různými verzemi).
- **Juraj má full-time job** — F2 spustit jen při jasném signálu z F1.
