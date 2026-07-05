# Pohoda Analytics (pracovní název)

Modulární BI nástroj pro uživatele IS POHODA. Cíl: majitel firmy rozumí svým
číslům za 10 minut — bez konzultanta, bez Excelu.

**Právní poznámka:** POHODA je ochranná známka STORMWARE s.r.o. Tento projekt
není produktem Stormware; finální brand bude vlastní (viz docs/STRATEGY.md).

## Struktura

| Cesta | Obsah |
|---|---|
| `app/` | Demo dashboard (statický SPA, vanilla JS + Chart.js) — Přehled, Prodej, Pohledávky & Závazky, Sklad, XML import |
| `connector/generate_demo_data.py` | Generátor dat fiktivní firmy → `app/data.js` |
| `connector/pohoda_xml_parser.py` | Parser Pohoda XML exportů (invoice/order/stock.xsd) → stejný datový model |
| `site/` | Návrh marketingové landing page |
| `docs/` | Strategie, konkurenční analýza (FameDash), architektura |

## Spuštění dema

```bash
python3 connector/generate_demo_data.py   # vygeneruje app/data.js
python3 -m http.server 4280 -d app        # http://localhost:4280
```

Vlastní data: v Pohodě `Soubor → Datová komunikace → XML export` (vydané
faktury), pak v dashboardu záložka **Napojení na Pohodu** → přetáhnout XML.
Zpracování probíhá jen v prohlížeči. Nebo přes CLI:

```bash
python3 connector/pohoda_xml_parser.py exporty/*.xml -o app/data.js --company "Moje firma"
```

## Stav a další kroky

Fáze F0 (demo) hotová. Další: F1 validace — viz [docs/STRATEGY.md](docs/STRATEGY.md).
