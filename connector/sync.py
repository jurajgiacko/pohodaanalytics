#!/usr/bin/env python3
"""
Konektor v1: Pohoda -> dashboard (lokálně) / cloud (později).

Běží na počítači, kde je nainstalovaná Pohoda (libovolná edice — MDB, SQL, E1).
Přes oficiální XML komunikaci (Pohoda.exe /XML) exportuje agendy, parsuje je
do jednotného datového modelu, aplikuje mapování dimenzí a zapíše data.js
pro dashboard (volitelně pošle na cloud API).

Použití:
    python3 sync.py --init                # průvodce vytvořením config.json
    python3 sync.py                       # plný sync (vyžaduje Windows + Pohodu)
    python3 sync.py --dry-run             # přeskočí Pohodu, parsuje existující
                                          # response XML v <data_dir>/responses
Plán: zabalit PyInstallerem do jednoho .exe bez závislosti na Pythonu.
"""

import argparse
import glob
import gzip
import json
import os
import subprocess
import sys
import urllib.request
from datetime import date

from pohoda_xml_parser import parse_file  # sdílený parser (invoice/order/stock)

CONFIG_DEFAULT = {
    "pohoda_exe": "C:\\Program Files (x86)\\STORMWARE\\POHODA\\Pohoda.exe",
    "pohoda_user": "@",
    "pohoda_password": "",
    "ico": "",
    "company": "Moje firma",
    "data_dir": ".",          # sem se zapisují requesty/response a výstup
    "years": [date.today().year - 1, date.today().year],
    "output": "data.js",
    "cloud": {"url": None, "api_key": None},
    "mapping": {
        "channels_by_number_prefix": {"*": "B2B"},
        "salespeople_by_centre": {"*": "Nepřiřazeno"},
    },
}

ENC = "Windows-1250"


def request_invoices(inv_type, year, req_id):
    return f"""<?xml version="1.0" encoding="{ENC}"?>
<dat:dataPack id="{req_id}" ico="{{ico}}" application="PohodaAnalytics" version="2.0" note="export {inv_type} {year}"
 xmlns:dat="http://www.stormware.cz/schema/version_2/data.xsd"
 xmlns:lst="http://www.stormware.cz/schema/version_2/list.xsd"
 xmlns:ftr="http://www.stormware.cz/schema/version_2/filter.xsd"
 xmlns:inv="http://www.stormware.cz/schema/version_2/invoice.xsd">
 <dat:dataPackItem id="{req_id}-1" version="2.0">
  <lst:listInvoiceRequest version="2.0" invoiceType="{inv_type}" invoiceVersion="2.0">
   <lst:requestInvoice>
    <ftr:filter>
     <ftr:dateFrom>{year}-01-01</ftr:dateFrom>
     <ftr:dateTill>{year}-12-31</ftr:dateTill>
    </ftr:filter>
   </lst:requestInvoice>
  </lst:listInvoiceRequest>
 </dat:dataPackItem>
</dat:dataPack>"""


def request_orders(year, req_id):
    return f"""<?xml version="1.0" encoding="{ENC}"?>
<dat:dataPack id="{req_id}" ico="{{ico}}" application="PohodaAnalytics" version="2.0" note="export objednavek {year}"
 xmlns:dat="http://www.stormware.cz/schema/version_2/data.xsd"
 xmlns:lst="http://www.stormware.cz/schema/version_2/list.xsd"
 xmlns:ftr="http://www.stormware.cz/schema/version_2/filter.xsd"
 xmlns:ord="http://www.stormware.cz/schema/version_2/order.xsd">
 <dat:dataPackItem id="{req_id}-1" version="2.0">
  <lst:listOrderRequest version="2.0" orderType="receivedOrder" orderVersion="2.0">
   <lst:requestOrder>
    <ftr:filter>
     <ftr:dateFrom>{year}-01-01</ftr:dateFrom>
     <ftr:dateTill>{year}-12-31</ftr:dateTill>
    </ftr:filter>
   </lst:requestOrder>
  </lst:listOrderRequest>
 </dat:dataPackItem>
</dat:dataPack>"""


def request_stock(req_id):
    return f"""<?xml version="1.0" encoding="{ENC}"?>
<dat:dataPack id="{req_id}" ico="{{ico}}" application="PohodaAnalytics" version="2.0" note="export skladu"
 xmlns:dat="http://www.stormware.cz/schema/version_2/data.xsd"
 xmlns:lStk="http://www.stormware.cz/schema/version_2/list_stock.xsd"
 xmlns:ftr="http://www.stormware.cz/schema/version_2/filter.xsd"
 xmlns:stk="http://www.stormware.cz/schema/version_2/stock.xsd">
 <dat:dataPackItem id="{req_id}-1" version="2.0">
  <lStk:listStockRequest version="2.0" stockVersion="2.0">
   <lStk:requestStock/>
  </lStk:listStockRequest>
 </dat:dataPackItem>
</dat:dataPack>"""


def build_requests(cfg):
    """Vytvoří request XML soubory + command file pro Pohoda.exe (messages.xsd)."""
    req_dir = os.path.join(cfg["data_dir"], "requests")
    resp_dir = os.path.join(cfg["data_dir"], "responses")
    os.makedirs(req_dir, exist_ok=True)
    os.makedirs(resp_dir, exist_ok=True)

    reqs = []
    for year in cfg["years"]:
        reqs.append((f"fv_{year}", request_invoices("issuedInvoice", year, f"fv{year}")))
        reqs.append((f"fp_{year}", request_invoices("receivedInvoice", year, f"fp{year}")))
        reqs.append((f"obj_{year}", request_orders(year, f"obj{year}")))
    reqs.append(("sklad", request_stock("stk")))

    run_items = []
    for name, xml in reqs:
        path = os.path.join(req_dir, f"{name}.xml")
        with open(path, "w", encoding=ENC, errors="replace") as f:
            f.write(xml.replace("{ico}", cfg["ico"]))
        resp = os.path.join(resp_dir, f"{name}.xml")
        run_items.append(f'  <mSk:runXML id="{name}" input="{path}" output="{resp}" ico="{cfg["ico"]}"/>')

    command_file = os.path.join(cfg["data_dir"], "command.xml")
    with open(command_file, "w", encoding=ENC) as f:
        f.write(f"""<?xml version="1.0" encoding="{ENC}"?>
<mSk:messages xmlns:mSk="http://www.stormware.cz/schema/messages.xsd">
{chr(10).join(run_items)}
</mSk:messages>""")
    return command_file, resp_dir


def run_pohoda(cfg, command_file):
    cmd = [cfg["pohoda_exe"], "/XML", cfg["pohoda_user"], cfg["pohoda_password"], command_file]
    print(f"Spouštím: {cfg['pohoda_exe']} /XML ... {command_file}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        sys.exit(f"Pohoda.exe skončila chybou {result.returncode}:\n{result.stderr or result.stdout}")


def apply_mapping(data, mapping):
    """Univerzální dimenze: kanál z prefixu číselné řady, obchodník ze střediska."""
    ch_map = mapping.get("channels_by_number_prefix", {})
    sp_map = mapping.get("salespeople_by_centre", {})

    def lookup(m, key):
        for prefix, label in m.items():
            if prefix != "*" and key and key.startswith(prefix):
                return label
        return m.get("*")

    for inv in data["invoices_issued"]:
        sp = lookup(sp_map, inv.get("centre") or "")
        inv.setdefault("salesperson", sp)
        channel = lookup(ch_map, inv.get("number", ""))
        if channel:
            inv["segment"] = channel
    return data


def push_cloud(cfg, data):
    url, key = cfg["cloud"].get("url"), cfg["cloud"].get("api_key")
    if not url:
        return
    body = gzip.compress(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Content-Encoding": "gzip",
        "Authorization": f"Bearer {key}",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        print(f"Cloud sync: HTTP {r.status}")


def init_config(path):
    cfg = dict(CONFIG_DEFAULT)
    print("— Průvodce nastavením konektoru —")
    for key, prompt in [("pohoda_exe", "Cesta k Pohoda.exe"), ("pohoda_user", "Uživatel Pohody"),
                        ("pohoda_password", "Heslo"), ("ico", "IČO účetní jednotky"),
                        ("company", "Název firmy")]:
        val = input(f"{prompt} [{cfg[key]}]: ").strip()
        if val:
            cfg[key] = val
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"Uloženo do {path}. Spusťte: python3 sync.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "config.json"))
    ap.add_argument("--init", action="store_true", help="vytvořit config.json průvodcem")
    ap.add_argument("--dry-run", action="store_true", help="neexportovat z Pohody, jen parsovat responses/")
    args = ap.parse_args()

    if args.init:
        init_config(args.config)
        return

    if not os.path.exists(args.config):
        sys.exit(f"Chybí {args.config} — spusťte nejdřív: python3 sync.py --init")
    with open(args.config, encoding="utf-8") as f:
        cfg = {**CONFIG_DEFAULT, **json.load(f)}

    command_file, resp_dir = build_requests(cfg)
    if not args.dry_run:
        if os.name != "nt":
            sys.exit("Plný sync běží jen na Windows s Pohodou. Použijte --dry-run pro test parsování.")
        run_pohoda(cfg, command_file)

    data = {
        "meta": {"company": cfg["company"], "ico": cfg["ico"], "currency": "CZK",
                 "generated": date.today().isoformat(), "source": "pohoda-connector",
                 "period_from": None, "period_to": date.today().isoformat()},
        "bank_accounts": [], "invoices_issued": [], "invoices_received": [],
        "orders": [], "stock": [],
    }
    files = sorted(glob.glob(os.path.join(resp_dir, "*.xml")))
    if not files:
        sys.exit(f"Žádné response XML v {resp_dir}.")
    for f in files:
        counts = parse_file(f, data)
        print(f"{os.path.basename(f)}: {counts}")

    dates = [i["date"] for i in data["invoices_issued"] + data["invoices_received"] if i["date"]]
    if dates:
        data["meta"]["period_from"] = min(dates)

    data = apply_mapping(data, cfg["mapping"])

    out = os.path.join(cfg["data_dir"], cfg["output"])
    with open(out, "w", encoding="utf-8") as f:
        f.write("// Vygenerováno konektorem sync.py\nwindow.DEMO_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"OK: {len(data['invoices_issued'])} FV, {len(data['invoices_received'])} FP, "
          f"{len(data['orders'])} OBJ, {len(data['stock'])} skladových položek -> {out}")

    push_cloud(cfg, data)


if __name__ == "__main__":
    main()
