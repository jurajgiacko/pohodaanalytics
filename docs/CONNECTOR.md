# Konektor: jak dostat data z Pohody (rozhodnutí)

## Možnosti přístupu k datům Pohody

| Cesta | Funguje na | Instalace u zákazníka | Rizika | Verdikt |
|---|---|---|---|---|
| **1. Ruční XML export** (Soubor → Datová komunikace) | všechny edice (MDB, SQL, E1) | žádná — drag & drop do prohlížeče | ruční práce, data stárnou | ✅ trial / free tarif (hotové v F0) |
| **2. `pohoda.exe /XML`** — automatizovaná XML komunikace | všechny edice | konektor + účet v Pohodě | Pohoda musí být na disku dostupná; oficiální, dokumentované schéma Stormware | ✅ **konektor v1 — hlavní cesta** |
| **3. mServer** (HTTP API Pohody) | všechny edice, běží jako služba | nutné nakonfigurovat mServer v Pohodě (instance, port, uživatel) | u Vitaru reálně: „čaká sa na credentials a IP whitelist" — síťová konfigurace je bariéra | ⏫ v2 upgrade pro náročné (častější sync, zápis) |
| **4. Přímé čtení SQL/MDB** (cesta FameBee) | jen SQL/E1 pro SQL Server | přístup k DB | nedokumentované schéma, rozbije se s update Pohody, licenčně šedá zóna | ❌ ne |

**Klíčový poznatek:** i mServer je jen lokální HTTP server — cloud se k němu za NATem
stejně nedostane. Konektor u zákazníka je potřeba v každém případě. Rozdíl mezi
cestou 2 a 3 je jen v tom, jak konektor mluví s Pohodou lokálně. Proto:
konektor navrhujeme tak, aby uměl obě, a začínáme cestou 2 (nula konfigurace v Pohodě).

## Architektura konektoru v1

```
[PC/server se Pohodou]
  sync.py (později PyInstaller .exe)
    1. vygeneruje XML requesty (listInvoice, listOrder, listStock)
    2. spustí Pohoda.exe /XML  →  response XML
    3. parsuje (pohoda_xml_parser.py) → jednotný datový model
    4. aplikuje mapování dimenzí (číselné řady → kanály, střediska → obchodníci)
    5a. zapíše data.js (lokální dashboard)                — funguje UŽ TEĎ
    5b. POST gzip JSON na cloud ingest API (API klíč)     — až bude cloud (F2)
  Task Scheduler: každou hodinu (install.bat to nastaví)
```

Instalační zážitek, na který míříme (v1 → v1.5):
1. Stáhnout `pohoda-analytics-setup.exe` (PyInstaller, žádný Python).
2. Průvodce: cesta k Pohoda.exe → uživatel/heslo Pohody → IČO → párovací kód z webu.
3. Hotovo — konektor se zaregistruje do Task Scheduleru a od té chvíle syncuje.

## Univerzální moduly

Moduly nikdy nesahají na Pohodu přímo — konzumují **datový kontrakt v1**
(viz ARCHITECTURE.md). Cokoliv, co dodá kontraktní JSON (XML parser, mServer
klient, demo generátor, v budoucnu i jiný ERP), rozsvítí všechny moduly.

Firemní specifika řeší **mapování dimenzí** v `config.json`, ne kód:

```jsonc
"mapping": {
  "channels_by_number_prefix": { "112": "E-shop CZ", "122": "E-shop SK", "*": "B2B" },
  "salespeople_by_centre":     { "KPR": "Karolína", "JGO": "Jirka", "*": "Nepřiřazeno" }
}
```

To je zobecnění hardcode logiky z Vitar `analytics.py` (klasifikace kanálů
z číselných řad, obchodník ze střediska). V F2 se mapování edituje v UI.

## Co ověřit na prvních pilotech (F1)

- [ ] přesná syntaxe `Pohoda.exe /XML` na reálné instalaci (command file `messages.xsd`) — implementováno dle dokumentace Stormware, potřebuje ověření
- [ ] chování při zamčené/otevřené Pohodě (exkluzivní přístup MDB)
- [ ] výkon na velké agendě (Vitar: desítky tisíc faktur → OK, ale MDB edice?)
- [ ] kódování Windows-1250 v responsech starších verzí
- [ ] licence: XML komunikace je součást všech edic, ale ověřit počet přístupů
