# Roadmap & checklist — co všechno musíme podchytit

Živý dokument. Fáze F1 (validace) → F2 (placený SaaS) → F3 (růst).
Doplňuje STRATEGY.md (proč) a ARCHITECTURE.md (jak technicky).

## Platby & fakturace (F2, rozhodnout dřív)

- [ ] **Platební brána: Stripe Billing.** Subscriptions v CZK, proration při
  dokoupení účetní jednotky (+450 Kč vzor FameDash), dunning při neúspěšné
  platbě, self-service customer portal. GoPay/Comgate mají slabou podporu
  recurring — nebrat pro subscriptions.
- [ ] **Daňové doklady: Stripe → Fakturoid** (běžný CZ pattern). Stripe strhne
  platbu, Fakturoid vystaví fakturu s DPH. Sbírat IČO/DIČ při checkoutu.
- [ ] **Platba převodem na fakturu** pro roční tarify — česká B2B klasika,
  hlavně účetní kanceláře. Ručně přes Fakturoid, automatizovat až později.
- [ ] DPH režimy: CZ 21 %, SK zákazníci (OSS / reverse charge u plátců) — ověřit
  s účetní PŘED spuštěním prodeje.
- [ ] Ceník: roční −20 %, trial konektoru 14 dní, chování po nezaplacení
  (read-only režim 14 dní → suspend, nikdy nemazat data hned).
- [ ] **Z čeho fakturujeme:** živnost vs. s.r.o. — rozhodnout před prvním
  placeným zákazníkem (ručení, důvěryhodnost pro kanceláře).

## Právo & GDPR (F1 konec / F2 start)

- [ ] Obchodní podmínky (VOP) + Zásady ochrany osobních údajů.
- [ ] **DPA (smlouva o zpracování)** — u účetních dat nutnost, bude to první
  otázka každé kanceláře. Vzor + seznam sub-processorů (Vercel, Supabase,
  Stripe, Fakturoid, e-mail provider).
- [ ] Ochranná známka: finální brand, rešerše ÚPV, doména, registrace známky.
- [ ] Disclaimer STORMWARE všude (web ✓, app ✓, VOP, smlouvy).
- [ ] Licenční otázka: ověřit podmínky XML komunikace Pohody (počet přístupů,
  automatizace) — ideálně dotaz na Stormware / partnerský program POHODA Plus.

## Konektor (F2) — často zapomínané

- [ ] **Code signing certifikát pro Windows .exe** — bez podpisu SmartScreen
  konektor zablokuje a pilot skončí dřív, než začal. (EV cert ~300 €/rok,
  vyřízení trvá týdny → objednat brzy.)
- [ ] Auto-update konektoru (jinak navždy podporujeme v1).
- [ ] Error reporting (Sentry) + lokální log, ať support nezačíná otázkou
  „pošlete mi screenshot".
- [ ] Chování při zamčené Pohodě / spuštěné účetní závěrce — retry, ne pád.
- [ ] Odolnost: výpadek internetu → doženě při dalším běhu; nikdy neposílat
  duplicitně (idempotentní ingest).

## Cloud & provoz (F2)

- [ ] Ingest API + Postgres schéma s RLS per workspace (viz ARCHITECTURE.md).
- [ ] Zálohy DB + **otestovaný restore** (záloha bez testu obnovy neexistuje).
- [ ] Monitoring: uptime (BetterStack/UptimeRobot), chybovost API, stáří dat
  per zákazník (nejčastější support ticket bude „nemám čerstvá čísla").
- [ ] Transakční e-maily (Resend/Postmark) + SPF/DKIM na vlastní doméně:
  pozvánky, párovací kódy, dunning, týdenní digest.
- [ ] Rate limiting a API klíče s možností revokace (✓ návrh v sync.py).
- [ ] EU region všude (Vercel fra1, Supabase EU).

## Web & marketing (průběžně)

- [ ] Web analytics: **Plausible/Simple Analytics** — GDPR-friendly, bez cookie
  lišty. GA4 nebrat kvůli liště na marketing webu.
- [ ] Doména + e-mail (hello@…) po rozhodnutí brandu; přesměrovat vercel.app.
- [ ] OG image (obrázek pro sdílení), sitemap.xml, robots.txt.
- [ ] Měření funnelu: návštěva → demo → XML import → e-mail (pilot signup).
- [ ] Nápověda/dokumentace (návod XML export z Pohody se screenshoty = zároveň
  SEO obsah), FAQ rozšířit podle reálných dotazů pilotů.
- [ ] CRM pro piloty: zatím tabulka (kdo, verze Pohody, edice, stav, feedback).

## Podpora & onboarding (F2)

- [ ] Sdílená schránka (podpora@) + cílová reakční doba pro tarif Kancelář.
- [ ] Onboarding checklist v aplikaci (nainstaluj konektor → spáruj → pozvi kolegy).
- [ ] Video: 3min „od instalace k prvním číslům".
- [ ] Status page (i jednoduchá) — důvěra účetních kanceláří.

## Pořadí (návrh)

1. **Teď (F1):** brand + doména + ÚPV rešerše · rozhovory/piloti · návod XML
   exportu · analytics na web · CRM tabulka pilotů.
2. **Jakmile F1 potvrdí zájem:** živnost/s.r.o. + účetní konzultace DPH ·
   objednat code signing cert (dlouhé dodání!) · VOP + DPA draft.
3. **F2 build:** auth + workspace → ingest + DB → Stripe + Fakturoid →
   transakční e-maily → monitoring → beta s piloty → veřejné spuštění.
