# Mapa modulů: co přenést z Vitar Sport Analytics do produktu

Inventura všech funkcí ověřených v produkci na vytrvalci-pro.digital
(repo vitar-sport-analytics-claude) a jejich zobecnění pro produkt.
Priorita: **MVP** = musí být v placené verzi od začátku, **F2/F3** = později,
**NE** = nepřenášet.

## Views z Vitar dashboardu

| Vitar view | Co dělá | Zobecnění pro produkt | Priorita | Má FameDash? |
|---|---|---|---|---|
| Dashboard | KPI + přehled | **Přehled** (v F0 hotové) | MVP | ano (LeaderBI) |
| Objednávky | detail objednávek, filtry | **Objednávky** — stav vyřízení, konverze objednávka→faktura | MVP | částečně |
| Faktúry | úhrady, cash flow | **Pohledávky & Závazky** (v F0) + **Cash flow** (příjmy vs. výdaje po měsících) | MVP | ano |
| Sklad | zásoby + **predikce vyprodání** (`days_remaining`) | **Sklad** + predikce: rychlost prodeje → dny do vyprodání, návrh doplnění | MVP (predikce = diferenciace) | jen marže/obrátka |
| Plány | roční plán, rozpad na měsíce/kanály/obchodníky, plnění | **Plán & plnění** — plán vs. realita, tempo, forecast dojezdu roku | **MVP — killer feature** | NE ❗ |
| CRM / Zákazníci | účty zákazníků, YoY per zákazník | **Zákazníci** — YoY růst/pokles, noví vs. ztracení (churn), závislost na top N | MVP | jen kontakty |
| Top 10 / Značky / Kategórie | produktová analytika | **Produkty** — top produkty/kategorie, marže per produkt | MVP | přes FlexBoard (složité) |
| E-commerce (kanály, PNO) | plnění per e-shop, marketing/PNO (ads vs. tržby) | **E-commerce modul** — kanály podle číselných řad, PNO z reklamních exportů | F2 | jen GA4 v EXTRA |
| Report / Close (uzávěrka) | generovaný měsíční sumář | **Měsíční report** — PDF/e-mail digest jedním klikem | F2 | ne |
| Analytics (GA4) | web analytika | Marketing modul (GA4 API) | F3 | ano (EXTRA) |
| Sponzoring | tracking sponzorovaných subjektů | zobecnit jako "Projekty/střediska" (náklady na středisko Pohody) | F3 | ne |
| Events (predajné akcie) | tržby z akcí/exp | příliš specifické — řeší "Projekty/střediska" | NE | ne |

## Funkce mimo views (api/, skripty)

| Vitar funkce | Co dělá | Zobecnění | Priorita |
|---|---|---|---|
| `api/comments.py` + comments_*.js | sdílené komentáře k fakturám (Neon Postgres) | **Komentáře/poznámky** k faktuře/zákazníkovi — týmová spolupráce nad čísly | F2 |
| `api/export_receivables.py` | XLSX export pohledávek s agingem a komentáři | **Export upomínkového seznamu** (XLSX/PDF); později generátor upomínek | F2 |
| `create_order_plan.py` | forecast objednávek (YoY růst, 2letý trend) do Excelu | **Návrh nákupní objednávky** — co objednat dodavateli a kdy | F3 (diferenciace pro velkoobchody) |
| `analytics.py` klasifikace | kanály z číselných řad, obchodník z "kdo řeší"/střediska | **Konfigurovatelné dimenze**: mapování číselných řad → kanály, středisek → obchodníci (UI místo hardcode) | MVP (zjednodušeně), F2 (UI) |
| `api/pohoda.py` (mServer) | live dotazy na Pohodu | konektor F2/F3 (viz ARCHITECTURE.md) | F2/F3 |
| `update.command` + sync.bat | hodinový XML export → git → Vercel | konektor v1 (bez gitu, push na API) | F2 |
| `plan.js` struktura | roční plán → měsíce → kanály → obchodníci | datový model plánů (zadání v UI, ne v kódu) | MVP |

## Poučení z Vitaru, která šetří měsíce

1. **Zdroj pravdy jsou faktury, ne objednávky** — obraty reportovat z faktur,
   objednávky jen jako pipeline. (KNOWLEDGE_BASE §5.1)
2. **Kanály se poznají z číselných řad dokladů** (112xxx = e-shop CZ…) — v produktu
   to musí být nastavitelné mapování, každá firma čísluje jinak.
3. **Obchodník** = pole "kdo řeší"/středisko + výjimky per zákazník → potřeba
   override tabulky (u Vitaru hardcode, u nás UI).
4. **Měny a DPH režimy** (CZ s/bez DPH, SK) dělají v reportech největší zmatek —
   všechno přepočítávat do domácí měny a reportovat bez DPH, přepínač jen jako detail.
5. **Predikce skladu**: prodejní rychlost za posledních N dní → `days_remaining`
   — jednoduchý výpočet, obrovská vnímaná hodnota.
6. **Plnění plánu je nejpoužívanější view** — majitel se dívá každý den, jestli
   "jedeme na plán". FameDash tohle vůbec nemá → hlavní diferenciátor MVP.

## Cílová struktura modulů produktu

```
MVP:   Přehled · Prodej · Plán & plnění · Zákazníci · Produkty · Pohledávky & Závazky · Sklad (s predikcí) · Objednávky
F2:    Cash flow · Měsíční report (PDF/e-mail) · Komentáře · Upomínky · E-commerce (kanály + PNO) · konfigurace dimenzí v UI
F3:    AI vrstva (shrnutí, anomálie, NL dotazy) · Návrh nákupu · Marketing (GA4) · Projekty/střediska · white-label pro účetní
```
