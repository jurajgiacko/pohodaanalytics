#!/usr/bin/env python3
"""
Pohoda XML -> datový model dashboardu.

Parsuje XML exporty z IS POHODA (schémata Stormware version_2):
- vydané faktury  (invoice.xsd, invoiceType=issuedInvoice)
- přijaté faktury (invoice.xsd, invoiceType=receivedInvoice)
- přijaté objednávky (order.xsd)
- skladové zásoby (stock.xsd / list_stock.xsd)

Použití:
    python3 pohoda_xml_parser.py cesta/k/exportum/*.xml -o ../app/data.js
    python3 pohoda_xml_parser.py export.xml --json        # čistý JSON na stdout

Jde o první verzi konektoru: ručně exportovaná XML (Pohoda -> Soubor ->
Datová komunikace -> XML export). Další krok je automatický sync přes
mServer API (viz docs/ARCHITECTURE.md).
"""

import argparse
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import date

NS = {
    "dat": "http://www.stormware.cz/schema/version_2/data.xsd",
    "inv": "http://www.stormware.cz/schema/version_2/invoice.xsd",
    "ord": "http://www.stormware.cz/schema/version_2/order.xsd",
    "stk": "http://www.stormware.cz/schema/version_2/stock.xsd",
    "typ": "http://www.stormware.cz/schema/version_2/type.xsd",
    "lst": "http://www.stormware.cz/schema/version_2/list.xsd",
    "lsk": "http://www.stormware.cz/schema/version_2/list_stock.xsd",
}


def text(el, path):
    found = el.find(path, NS)
    return found.text.strip() if found is not None and found.text else None


def number(el, path):
    t = text(el, path)
    try:
        return float(t) if t else 0.0
    except ValueError:
        return 0.0


def parse_invoice(inv_el):
    """Jeden inv:invoice element -> dict datového modelu."""
    h = inv_el.find("inv:invoiceHeader", NS)
    if h is None:
        return None, None
    inv_type = text(h, "inv:invoiceType") or "issuedInvoice"
    partner_el = h.find("inv:partnerIdentity/typ:address", NS)
    summary = inv_el.find("inv:invoiceSummary", NS)
    home = summary.find("inv:homeCurrency", NS) if summary is not None else None

    total = 0.0
    if home is not None:
        total = sum(number(home, f"typ:{f}") for f in
                    ("priceNone", "priceLow", "priceLowVAT", "priceHigh", "priceHighVAT"))
        if total == 0:
            total = number(home, "typ:priceHighSum") + number(home, "typ:priceLowSum") + number(home, "typ:priceNoneSum")

    liq = h.find("inv:liquidation", NS)
    paid_date = text(liq, "typ:date") if liq is not None else text(h, "inv:dateOfPayment")

    items = []
    detail = inv_el.find("inv:invoiceDetail", NS)
    if detail is not None:
        for it in detail.findall("inv:invoiceItem", NS):
            qty = number(it, "inv:quantity")
            unit_price = number(it, "inv:homeCurrency/typ:unitPrice")
            items.append({
                "code": text(it, "inv:code") or "",
                "name": text(it, "inv:text") or "",
                "category": text(it, "inv:stockItem/typ:store/typ:ids") or "Ostatní",
                "qty": qty,
                "unit_price": unit_price,
                "total": number(it, "inv:homeCurrency/typ:priceSum") or qty * unit_price,
                "purchase_price": number(it, "inv:stockItem/typ:stockItem/typ:purchasingPrice"),
            })

    record = {
        "number": text(h, "inv:number/typ:numberRequested") or text(h, "inv:symVar") or "?",
        "date": text(h, "inv:date"),
        "due_date": text(h, "inv:dateDue") or text(h, "inv:date"),
        "partner": (text(partner_el, "typ:company") or text(partner_el, "typ:name") or "Neznámý") if partner_el is not None else "Neznámý",
        "ico": text(partner_el, "typ:ico") if partner_el is not None else None,
        "segment": text(h, "inv:centre/typ:ids") or "Bez segmentu",
        "total": round(total, 2),
        "currency": text(h, "inv:foreignCurrency/typ:currency/typ:ids") or "CZK",
        "paid": paid_date is not None,
        "paid_date": paid_date,
        "items": items or None,
    }
    return ("received" if "received" in inv_type else "issued"), record


def parse_order(ord_el):
    h = ord_el.find("ord:orderHeader", NS)
    if h is None:
        return None
    partner_el = h.find("ord:partnerIdentity/typ:address", NS)
    summary = ord_el.find("ord:orderSummary/typ:homeCurrency", NS)
    total = 0.0
    if summary is not None:
        total = sum(number(summary, f"typ:{f}") for f in
                    ("priceNone", "priceLow", "priceLowVAT", "priceHigh", "priceHighVAT"))
    done = text(h, "ord:isExecuted") == "true"
    return {
        "number": text(h, "ord:number/typ:numberRequested") or "?",
        "date": text(h, "ord:date"),
        "partner": (text(partner_el, "typ:company") or text(partner_el, "typ:name") or "Neznámý") if partner_el is not None else "Neznámý",
        "total": round(total, 2),
        "status": "vyřízená" if done else "nevyřízená",
    }


def parse_stock(stk_el):
    h = stk_el.find("stk:stockHeader", NS)
    if h is None:
        return None
    qty = number(h, "stk:count")
    purchase = number(h, "stk:purchasingPrice")
    return {
        "code": text(h, "stk:code") or "",
        "name": text(h, "stk:name") or "",
        "category": text(h, "stk:storage/typ:ids") or "Sklad",
        "qty": qty,
        "unit": text(h, "stk:unit") or "ks",
        "purchase_price": purchase,
        "selling_price": number(h, "stk:sellingPrice"),
        "value": round(qty * purchase, 2),
        "min_qty": number(h, "stk:limitMin"),
    }


def parse_file(path, data):
    tree = ET.parse(path)
    root = tree.getroot()
    all_els = root.iter()
    counts = {"issued": 0, "received": 0, "orders": 0, "stock": 0}
    for el in all_els:
        tag = el.tag.split("}")[-1]
        if tag == "invoice":
            kind, rec = parse_invoice(el)
            if rec and rec["date"]:
                data["invoices_issued" if kind == "issued" else "invoices_received"].append(rec)
                counts["issued" if kind == "issued" else "received"] += 1
        elif tag == "order":
            rec = parse_order(el)
            if rec and rec["date"]:
                data["orders"].append(rec)
                counts["orders"] += 1
        elif tag == "stock":
            rec = parse_stock(el)
            if rec:
                data["stock"].append(rec)
                counts["stock"] += 1
    return counts


def main():
    ap = argparse.ArgumentParser(description="Pohoda XML -> data.js pro dashboard")
    ap.add_argument("inputs", nargs="+", help="XML soubory nebo glob patterny")
    ap.add_argument("-o", "--output", default=None, help="výstupní data.js (default: stdout JSON)")
    ap.add_argument("--company", default="Moje firma", help="název firmy do hlavičky")
    ap.add_argument("--json", action="store_true", help="vypsat čistý JSON na stdout")
    args = ap.parse_args()

    files = []
    for pattern in args.inputs:
        files.extend(glob.glob(pattern))
    if not files:
        sys.exit("Žádné vstupní soubory nenalezeny.")

    data = {
        "meta": {
            "company": args.company,
            "currency": "CZK",
            "generated": date.today().isoformat(),
            "source": "pohoda-xml",
            "period_from": None,
            "period_to": date.today().isoformat(),
        },
        "bank_accounts": [],
        "invoices_issued": [],
        "invoices_received": [],
        "orders": [],
        "stock": [],
    }

    for f in sorted(files):
        counts = parse_file(f, data)
        print(f"{os.path.basename(f)}: {counts}", file=sys.stderr)

    dates = [i["date"] for i in data["invoices_issued"] + data["invoices_received"] if i["date"]]
    if dates:
        data["meta"]["period_from"] = min(dates)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("// Vygenerováno pohoda_xml_parser.py\nwindow.DEMO_DATA = ")
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            f.write(";\n")
        print(f"Zapsáno: {args.output}", file=sys.stderr)
    else:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
