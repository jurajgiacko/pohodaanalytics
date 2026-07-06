# Architektura

## Odkud jdeme (Vitar Sport Analytics)

Ověřený pattern: Pohoda E1 → XML export (Task Scheduler) → Python parser →
statická JS data → dashboard na Vercelu. Funguje léta v produkci, ale je
single-tenant, data jsou v gitu a logika je hardcodovaná na jednu firmu.
**Kód se nepřenáší, přenáší se know-how:** které přehledy se reálně používají,
Pohoda XML schémata, past na kódování/diakritiku, výkonové limity.

## F0/F1 — demo (tento repozitář)

```
connector/generate_demo_data.py   fiktivní firma -> app/data.js
connector/pohoda_xml_parser.py    Pohoda XML exporty -> data.js / JSON
app/                              statický SPA dashboard (vanilla JS + Chart.js)
site/                             marketingová landing page
```

- Vše client-side, žádný backend. Deploy = statický hosting (Vercel).
- XML import běží v prohlížeči (DOMParser) → trial bez registrace a bez GDPR rizika.
- Datový model (data.js) je stejný pro demo generátor, XML parser i budoucí API —
  to je kontrakt, na kterém stavíme dál.

## Datový model (kontrakt v1)

```jsonc
{
  "meta":  { "company", "ico", "currency", "generated", "source", "period_from", "period_to" },
  "bank_accounts":     [{ "name", "number", "balance", "currency" }],
  "invoices_issued":   [{ "number", "date", "due_date", "partner", "ico", "segment",
                          "total", "currency", "paid", "paid_date", "items": [
                          { "code", "name", "category", "qty", "unit_price", "total", "purchase_price" }]}],
  "invoices_received": [{ ...bez items }],
  "orders":            [{ "number", "date", "partner", "total", "status" }],
  "stock":             [{ "code", "name", "category", "qty", "unit", "purchase_price",
                          "selling_price", "value", "min_qty" }]
}
```

## F2 — MVP SaaS

```
[Pohoda u zákazníka]                         [Cloud]
  konektor (Python/Go, Windows service) ──►  Ingest API (POST /sync, API key)
  - naplánovaný XML export přes              │
    pohoda.exe /XML nebo mServer             ▼
  - diff + gzip + TLS                      Postgres (multi-tenant, RLS)
                                             │
                                             ▼
                                           Web app (Next.js) + Auth + billing
```

Rozhodnutí:
- **Konektor first, mServer later.** XML export funguje na všech verzích Pohody
  (MDB, SQL, E1) a nevyžaduje otevírat porty. mServer (live) je upgrade pro E1/SQL.
- **Jeden binární konektor bez konfigurace:** párovací kód z webu, zbytek si stáhne.
- **Analytika zůstává co nejvíc na klientovi** (agregace v prohlížeči nad
  před-agregovanými řezy z API) — rychlé UX, levný provoz.
- Stack: Next.js + Postgres (Neon/Supabase) + Vercel; konektor Python →
  PyInstaller exe (známé prostředí z Vitaru).

## Účty a přihlašování (F2)

Zásada: **trial nikdy nevyžaduje registraci** (XML v prohlížeči = hlavní
akviziční argument). Účty přicházejí až s konektorem a uloženými daty.

Datový model — všechno visí na workspace, ne na uživateli:

```
User ──< WorkspaceMember >── Workspace ──< AccountingUnit (účetní jednotka / 1 Pohoda)
         (role: owner/admin/           │
          member/read-only)            ├── ConnectorKey (API klíč z párovacího kódu)
                                       └── Subscription (tarif, billing metrika = počet ú.j.)
```

- Auth: **Supabase Auth** (e-mail + heslo, magic link, Google; 2FA pro tarif
  Kancelář). Vlastní správu hesel nestavět. RLS v Postgresu per workspace.
- Pozvánky do workspace e-mailem; per-modul oprávnění až ve F3.
- Konektor se nepřihlašuje jako člověk: jednorázový párovací kód z webu
  → API klíč vázaný na účetní jednotku (viz `connector/sync.py`, `cloud.api_key`).
  Revokace klíče = odpojení konektoru bez zásahu u zákazníka.
- F1 mezikrok pro piloty: privátní deploy per pilot (Vercel password protection),
  žádný účetní systém.

## F3 — rozšíření

- mServer live sync (hodinový → minutový refresh).
- AI vrstva: měsíční shrnutí, anomálie, NL dotazy (Claude API nad agregáty,
  nikdy nad surovými osobními daty).
- White-label reporty pro účetní kanceláře, plánovaný e-mail digest.
- Export PDF (board report) a Excel.

## Bezpečnost a GDPR (od F2)

- Data zákazníka = citlivá účetní data: šifrování at rest, EU region, RLS per tenant.
- Trial nikdy neukládá data na server (client-side parsing) — marketingová výhoda.
- Zpracovatelská smlouva (DPA) jako standardní součást obchodních podmínek.
