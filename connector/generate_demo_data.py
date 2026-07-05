#!/usr/bin/env python3
"""
Generátor demo dat pro dashboard.

Vytváří realistická data fiktivní české firmy (velkoobchod sportovní výživy)
ve stejném datovém modelu, jaký produkuje pohoda_xml_parser.py.
Výstup: ../app/data.js  (window.DEMO_DATA = {...})

Použití: python3 generate_demo_data.py
"""

import json
import random
import os
from datetime import date, timedelta

random.seed(42)

TODAY = date(2026, 7, 5)
MONTHS_BACK = 30  # ~2,5 roku historie kvůli meziročnímu srovnání

SALESPEOPLE = ["Petra Králová", "Jan Dvořák", "Martin Svoboda"]

PARTNERS = [
    # (název, IČO, segment, velikost 0-1)
    ("Sportisimo Distribuce s.r.o.", "25112233", "B2B řetězec", 1.0),
    ("Fitness Time a.s.", "27455812", "B2B řetězec", 0.85),
    ("BikePoint Group s.r.o.", "29033448", "B2B řetězec", 0.8),
    ("Decario Sport s.r.o.", "24881190", "B2B řetězec", 0.7),
    ("Aktin Trade s.r.o.", "26904312", "B2B eshop", 0.65),
    ("RunSport Praha s.r.o.", "27600415", "B2B nezávislý", 0.5),
    ("Cyklo Novák s.r.o.", "26118834", "B2B nezávislý", 0.45),
    ("Outdoor Centrum Brno s.r.o.", "25990621", "B2B nezávislý", 0.42),
    ("Hory a sport s.r.o.", "28455710", "B2B nezávislý", 0.4),
    ("TriExpert s.r.o.", "24101577", "B2B nezávislý", 0.38),
    ("Fit Ostrava s.r.o.", "28617442", "B2B nezávislý", 0.35),
    ("Sportclub Plzeň s.r.o.", "26339811", "B2B nezávislý", 0.32),
    ("Maratonec.cz s.r.o.", "27118845", "B2B eshop", 0.3),
    ("Posilovna Zlín s.r.o.", "29455663", "B2B nezávislý", 0.25),
    ("SkiService Liberec s.r.o.", "25774491", "B2B nezávislý", 0.22),
    ("Wellness Hotel Sázava a.s.", "26005588", "HoReCa", 0.2),
    ("Lékárna U Anděla s.r.o.", "27334455", "Lékárny", 0.18),
    ("Fitness Lady Pardubice s.r.o.", "28990011", "B2B nezávislý", 0.15),
    ("Sokol Hradec Králové z.s.", "00448812", "Kluby", 0.12),
    ("TJ Slavoj Český Krumlov z.s.", "00551123", "Kluby", 0.1),
]

SUPPLIERS = [
    ("NutriPro Manufacturing GmbH", "DE811223344", 0.9),
    ("Balírny Vysočina s.r.o.", "25661788", 0.6),
    ("Obaly CZ s.r.o.", "27441005", 0.4),
    ("Přepravní služby Novotný s.r.o.", "28112277", 0.35),
    ("Marketing Hub s.r.o.", "26887711", 0.3),
    ("Energie Pro a.s.", "25100299", 0.25),
    ("IT Servis Morava s.r.o.", "29334410", 0.15),
]

PRODUCTS = [
    # (kód, název, kategorie, nákupní, prodejní)
    ("ION-500-CIT", "Iontový nápoj 500g citron", "Nápoje", 89, 189),
    ("ION-500-POM", "Iontový nápoj 500g pomeranč", "Nápoje", 89, 189),
    ("ION-1000-CIT", "Iontový nápoj 1kg citron", "Nápoje", 149, 319),
    ("GEL-ENE-32", "Energetický gel 32g", "Gely", 14, 32),
    ("GEL-KOF-32", "Energetický gel s kofeinem 32g", "Gely", 16, 36),
    ("BAR-PROT-55", "Proteinová tyčinka 55g", "Tyčinky", 18, 42),
    ("BAR-CER-45", "Cereální tyčinka 45g", "Tyčinky", 11, 26),
    ("PROT-WHEY-1K", "Syrovátkový protein 1kg", "Proteiny", 320, 649),
    ("PROT-WHEY-2K", "Syrovátkový protein 2kg", "Proteiny", 590, 1190),
    ("CREA-500", "Kreatin monohydrát 500g", "Suplementy", 210, 429),
    ("MAG-LIQ-25", "Magnesium liquid 25ml", "Suplementy", 12, 29),
    ("BCAA-300", "BCAA 300 tablet", "Suplementy", 240, 490),
    ("VIT-C-100", "Vitamin C 100 tablet", "Vitamíny", 45, 99),
    ("VIT-D3-90", "Vitamin D3 90 kapslí", "Vitamíny", 52, 115),
    ("MULTI-60", "Multivitamin 60 tablet", "Vitamíny", 68, 145),
    ("REG-DRINK-500", "Regenerační nápoj 500g", "Nápoje", 175, 359),
    ("BID-750", "Bidon 750ml", "Doplňky", 35, 89),
    ("SHAK-600", "Šejkr 600ml", "Doplňky", 42, 109),
]

def month_iter(n_back):
    y, m = TODAY.year, TODAY.month
    months = []
    for i in range(n_back, -1, -1):
        mm = m - i
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        months.append((yy, mm))
    return months

def season_factor(month):
    # sportovní výživa: jaro/léto silné, prosinec B2B předzásobení
    return {1: 0.75, 2: 0.85, 3: 1.0, 4: 1.15, 5: 1.25, 6: 1.2,
            7: 1.05, 8: 1.1, 9: 1.15, 10: 0.95, 11: 0.85, 12: 1.05}[month]

def growth_factor(y, m):
    # firma roste ~12 % ročně
    months_from_start = (y - 2024) * 12 + m
    return 1.0 * (1.01 ** months_from_start)

# každý partner má přiřazeného obchodníka (v Pohodě pole "středisko" / "kdo řeší")
PARTNER_SALESPERSON = {p[0]: SALESPEOPLE[i % len(SALESPEOPLE)] for i, p in enumerate(PARTNERS)}

invoices_issued = []
invoices_received = []
orders = []
inv_no = 24000001
ord_no = 124000001
rcv_no = 3240001

for (y, m) in month_iter(MONTHS_BACK):
    base_count = 38
    count = max(8, int(random.gauss(base_count * season_factor(m) * growth_factor(y, m) / 1.25, 5)))
    last_day = 28 if m == 2 else 30
    for _ in range(count):
        partner = random.choices(PARTNERS, weights=[p[3] for p in PARTNERS])[0]
        d = date(y, m, random.randint(1, last_day))
        if d > TODAY:
            continue
        # položky faktury
        n_items = random.randint(2, 8)
        items = []
        total = 0
        for _ in range(n_items):
            prod = random.choice(PRODUCTS)
            qty = random.choice([24, 48, 96, 144, 288]) if prod[4] < 200 else random.choice([6, 12, 24, 48])
            # B2B cena: sleva z MOC podle velikosti partnera (větší partner = větší sleva),
            # vždy nad nákupní cenou
            discount_mult = 0.58 + 0.18 * (1 - partner[3]) + random.uniform(-0.03, 0.05)
            price = round(max(prod[4] * discount_mult, prod[3] * 1.12), 2)
            items.append({"code": prod[0], "name": prod[1], "category": prod[2],
                          "qty": qty, "unit_price": price, "total": round(qty * price, 2),
                          "purchase_price": prod[3]})
            total += qty * price
        total = round(total, 2)
        due = d + timedelta(days=random.choice([14, 14, 30, 30, 30, 60]))
        # platební morálka: velcí platí hůř
        if due < TODAY - timedelta(days=120):
            paid_prob = 0.99
        elif due < TODAY - timedelta(days=5):
            paid_prob = 0.94
        else:
            paid_prob = 0.55
        paid = random.random() < paid_prob
        paid_date = None
        if paid:
            delay = int(abs(random.gauss(2, 12)))
            paid_date = min(due + timedelta(days=delay), TODAY)
            if paid_date > TODAY:
                paid = False
                paid_date = None
        invoices_issued.append({
            "number": str(inv_no), "date": d.isoformat(), "due_date": due.isoformat(),
            "partner": partner[0], "ico": partner[1], "segment": partner[2],
            "salesperson": PARTNER_SALESPERSON[partner[0]],
            "total": total, "currency": "CZK",
            "paid": paid, "paid_date": paid_date.isoformat() if paid_date else None,
            "items": items,
        })
        inv_no += 1

    # přijaté faktury (náklady ~72 % obratu)
    month_revenue = sum(i["total"] for i in invoices_issued if i["date"].startswith(f"{y:04d}-{m:02d}"))
    remaining = month_revenue * random.uniform(0.66, 0.78)
    while remaining > 20000:
        sup = random.choices(SUPPLIERS, weights=[s[2] for s in SUPPLIERS])[0]
        amount = round(min(remaining, abs(random.gauss(120000, 90000)) + 8000), 2)
        remaining -= amount
        d = date(y, m, random.randint(1, last_day))
        if d > TODAY:
            continue
        due = d + timedelta(days=random.choice([14, 30, 30, 45]))
        paid = due < TODAY - timedelta(days=3) and random.random() < 0.97 or (due >= TODAY and random.random() < 0.4)
        invoices_received.append({
            "number": str(rcv_no), "date": d.isoformat(), "due_date": due.isoformat(),
            "partner": sup[0], "ico": sup[1], "total": amount, "currency": "CZK",
            "paid": bool(paid),
            "paid_date": min(due + timedelta(days=int(abs(random.gauss(0, 5)))), TODAY).isoformat() if paid else None,
        })
        rcv_no += 1

    # objednávky (mírně víc než faktur — část nevyřízená)
    for _ in range(int(count * 1.12)):
        partner = random.choices(PARTNERS, weights=[p[3] for p in PARTNERS])[0]
        d = date(y, m, random.randint(1, last_day))
        if d > TODAY:
            continue
        total = round(abs(random.gauss(48000, 35000)) + 3000, 2)
        age = (TODAY - d).days
        status = "vyřízená" if age > 14 or random.random() < 0.6 else ("částečně" if random.random() < 0.3 else "nevyřízená")
        orders.append({"number": str(ord_no), "date": d.isoformat(), "partner": partner[0],
                       "total": total, "status": status})
        ord_no += 1

# sklad
stock = []
for (code, name, cat, buy, sell) in PRODUCTS:
    qty = random.randint(40, 2500)
    stock.append({
        "code": code, "name": name, "category": cat, "qty": qty, "unit": "ks",
        "purchase_price": buy, "selling_price": sell,
        "value": round(qty * buy, 2),
        "min_qty": random.choice([50, 100, 200]),
    })

# plány: minulý rok × růstový cíl, rozpad na měsíce a obchodníky
def build_plan(plan_year, growth):
    prev = plan_year - 1
    monthly_actual = {}
    sp_actual = {sp: 0.0 for sp in SALESPEOPLE}
    for i in invoices_issued:
        if i["date"].startswith(str(prev)):
            ym_m = int(i["date"][5:7])
            monthly_actual[ym_m] = monthly_actual.get(ym_m, 0) + i["total"]
            sp_actual[i["salesperson"]] += i["total"]
    if not monthly_actual:
        return None
    monthly = {f"{plan_year}-{m:02d}": round(monthly_actual.get(m, 0) * growth, -3) for m in range(1, 13)}
    annual = round(sum(monthly.values()), -3)
    prev_total = sum(sp_actual.values()) or 1
    salespeople = {sp: round(annual * v / prev_total, -3) for sp, v in sp_actual.items()}
    return {"annual": annual, "growth_target": round(growth - 1, 2),
            "monthly": monthly, "salespeople": salespeople}

plans = {}
for y, g in ((2025, 1.12), (2026, 1.15)):
    p = build_plan(y, g)
    if p:
        plans[str(y)] = p

data = {
    "meta": {
        "company": "Demo Sport Distribuce s.r.o.",
        "ico": "12345678",
        "currency": "CZK",
        "generated": TODAY.isoformat(),
        "source": "demo",
        "period_from": f"{month_iter(MONTHS_BACK)[0][0]}-{month_iter(MONTHS_BACK)[0][1]:02d}-01",
        "period_to": TODAY.isoformat(),
    },
    "bank_accounts": [
        {"name": "KB běžný účet", "number": "115-4433221100/0100", "balance": 2384500.20, "currency": "CZK"},
        {"name": "Fio EUR účet", "number": "2500998877/2010", "balance": 18420.55, "currency": "EUR"},
        {"name": "Pokladna", "number": "-", "balance": 48210.00, "currency": "CZK"},
    ],
    "plan": plans,
    "invoices_issued": invoices_issued,
    "invoices_received": invoices_received,
    "orders": orders,
    "stock": stock,
}

out_path = os.path.join(os.path.dirname(__file__), "..", "app", "data.js")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.write("// Vygenerováno connector/generate_demo_data.py — demo data fiktivní firmy\n")
    f.write("window.DEMO_DATA = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print(f"OK: {len(invoices_issued)} vydaných faktur, {len(invoices_received)} přijatých, "
      f"{len(orders)} objednávek, {len(stock)} skladových položek -> {os.path.abspath(out_path)}")
