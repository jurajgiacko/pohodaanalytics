# Konkurenční analýza: FameDash (Fameless s.r.o.)

*Stav k 2026-07-05, zdroj: demodash.fameless.cz (demo účet) + fameless.cz*

## Co FameDash je

Webová platforma (Laravel + Inertia/Vue + PrimeVue) napojená na IS POHODA přes
vlastní konektor **FameBee**. Multi-tenant: workspace → moduly → uživatelé s rolemi.
Konektor čte přímo SQL agendy Pohody (widgety se konfigurují nad tabulkami
`obj_prijata`, `fa_vydana` apod. včetně raw sloupců `datstorn`, `datsplat`, `vyrizeno`).

## Moduly

| Modul | Co dělá |
|---|---|
| **LeaderBI** | Management přehledy: finance (cashflow, banka), sklad (marže, obrátka, záporné zásoby), výsledovka, rozvaha, pohledávky/závazky, obchodní kontakty. Meziroční srovnání až od tarifu PRO. |
| **FlexBoard** | Widget builder — počítadla, grafy, tabulky, obrat kumulativně, marže dokladů. Uživatel skládá vlastní dashboardy nad agendami Pohody s podmínkami (filtr sloupec/operátor/hodnota). |
| **FameDog** | AI import dokladů do Pohody: upload PDF/CSV/ISDOC, e-mail mining, mapování, schvalovací workflow, párování na objednávky. Zpoplatněno po dokladech. |
| **Marketing** | Napojení GA4: návštěvnost, akvizice, PPC, tržby. Jen v tarifu EXTRA. |
| ServisDash, StorageMonkey (WMS) | Samostatné produkty mimo FameDash fee. |

## Ceník (bez DPH, měsíčně)

| Tarif | Cena | Účetní jednotky | Uživatelé | Poznámky |
|---|---|---|---|---|
| START | 1 890 Kč | 1 | 3 | LeaderBI bez meziročního srovnání, FameDog 100 dokladů |
| PRO | 3 490 Kč | 2 (+450 Kč/další) | 4–9 | plné LeaderBI, FameDog 250 dokladů |
| EXTRA | 4 190 Kč | 3 (+450 Kč/další) | 10–20 (+250 Kč/další) | + Marketing GA4, FameDog 500 dokladů |

Další byznys: jednorázové konfigurace (1 580 Kč/h), školení (25–50 tis. Kč/den),
WMS s pořizovací cenou 90 tis. Kč. Partnerský program existuje.

## Silné stránky

- Reálný konektor na SQL Pohody → live data, žádné ruční exporty.
- FameDog (AI importy dokladů) je samostatný revenue stream a silný akviziční kanál
  přes účetní kanceláře.
- Etablovaná firma s případovými studiemi (Ekokoza, V-Elektra, Atreon…), YouTube, podpora.
- Widget builder je flexibilní (v demu ale vyžaduje znalost struktur Pohody).

## Slabiny / příležitosti pro nás

1. **Vstupní cena.** 1 890 Kč/měs. je pro malou s.r.o. hodně. Prostor pro tarif
   ~490–990 Kč nebo freemium s ručním XML importem.
2. **Onboarding.** FameBee vyžaduje instalaci + konfiguraci od dodavatele; widget builder
   pracuje s raw SQL sloupci (`datstorn`, `relstorn`) — pro neajťáky nesrozumitelné.
   Náš cíl: hotové přehledy do 10 minut bez konzultanta, bez znalosti struktur.
3. **UX / rychlost.** Klasická server-side aplikace; každý widget = API call.
   Client-side analytika (náš přístup) je okamžitá — filtry a přepínání bez čekání.
4. **Bez AI vrstvy nad reporty.** FameDog = AI na importy, ale chybí "zeptej se svých dat"
   (přirozený jazyk → odpověď/graf), automatické komentáře k výsledkům, anomálie, forecast.
5. **Vizuální kvalita reportů.** Prostor odlišit se úrovní designu a "board-ready"
   exporty (PDF report pro jednatele/banku jedním klikem).
6. **Jen CZ trh.** Pohoda má i SK zákazníky (a mServer je stejný) — SK lokalizace levná.

## Co si vzít jako laťku

- Multi-tenant workspaces s per-modul přístupy.
- Meziroční srovnání jako placený trigger (funguje jim jako upsell do PRO).
- Zpoplatnění po účetních jednotkách — přirozená metrika pro účetní kanceláře.
