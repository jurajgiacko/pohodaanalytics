/* Pohoda Analytics — demo MVP
 * Čistě klientská aplikace: data.js (demo / import XML) -> analytika -> vizualizace.
 */

const DATA = window.DEMO_DATA;
const TODAY = DATA.meta.period_to;
const EUR_CZK = 24.8;

const fmtK = new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 0 });
const czk = (v) => fmtK.format(Math.round(v)) + " Kč";
const czkShort = (v) => {
  if (Math.abs(v) >= 1e6) return (v / 1e6).toLocaleString("cs-CZ", { maximumFractionDigits: 1 }) + " mil.";
  if (Math.abs(v) >= 1e3) return fmtK.format(v / 1e3) + " tis.";
  return fmtK.format(v);
};
const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString("cs-CZ") : "—";
const monthLabel = (ym) => {
  const [y, m] = ym.split("-");
  return ["led", "úno", "bře", "dub", "kvě", "čvn", "čvc", "srp", "zář", "říj", "lis", "pro"][+m - 1] + " " + y.slice(2);
};

/* ---------- period filter ---------- */
const PERIODS = [
  { id: "12m", label: "12 měsíců" },
  { id: "2026", label: "2026" },
  { id: "2025", label: "2025" },
  { id: "2024", label: "2024" },
  { id: "all", label: "Vše" },
];
let period = "12m";

function periodRange(p) {
  if (p === "all") return ["0000-01-01", "9999-12-31"];
  if (p === "12m") {
    const d = new Date(TODAY); d.setMonth(d.getMonth() - 11); d.setDate(1);
    return [d.toISOString().slice(0, 10), TODAY];
  }
  return [`${p}-01-01`, `${p}-12-31`];
}
function prevRange(p) {
  if (p === "all") return null;
  if (p === "12m") {
    const [from] = periodRange(p);
    const d = new Date(from); d.setFullYear(d.getFullYear() - 1);
    const e = new Date(TODAY); e.setFullYear(e.getFullYear() - 1);
    return [d.toISOString().slice(0, 10), e.toISOString().slice(0, 10)];
  }
  const y = +p - 1;
  // srovnatelné období: u běžícího roku jen do dnešního dne loňska
  if (p === String(new Date(TODAY).getFullYear())) {
    const e = new Date(TODAY); e.setFullYear(y);
    return [`${y}-01-01`, e.toISOString().slice(0, 10)];
  }
  return [`${y}-01-01`, `${y}-12-31`];
}
const inRange = (date, [from, to]) => date >= from && date <= to;

/* ---------- analytika ---------- */
function sum(arr, f = (x) => x.total) { return arr.reduce((a, b) => a + f(b), 0); }

function monthly(invoices, range) {
  const map = new Map();
  for (const i of invoices) {
    if (!inRange(i.date, range)) continue;
    const ym = i.date.slice(0, 7);
    map.set(ym, (map.get(ym) || 0) + i.total);
  }
  return [...map.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1);
}

function topBy(invoices, range, key, n = 10) {
  const map = new Map();
  for (const i of invoices) {
    if (!inRange(i.date, range)) continue;
    map.set(i[key], (map.get(i[key]) || 0) + i.total);
  }
  return [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);
}

function categorySales(range) {
  const map = new Map();
  for (const i of DATA.invoices_issued) {
    if (!inRange(i.date, range) || !i.items) continue;
    for (const it of i.items) map.set(it.category, (map.get(it.category) || 0) + it.total);
  }
  return [...map.entries()].sort((a, b) => b[1] - a[1]);
}

function agingBuckets(invoices) {
  const buckets = { "před splatností": 0, "1–30 dní": 0, "31–60 dní": 0, "61–90 dní": 0, "90+ dní": 0 };
  const today = new Date(TODAY);
  for (const i of invoices) {
    if (i.paid) continue;
    const days = Math.floor((today - new Date(i.due_date)) / 864e5);
    if (days <= 0) buckets["před splatností"] += i.total;
    else if (days <= 30) buckets["1–30 dní"] += i.total;
    else if (days <= 60) buckets["31–60 dní"] += i.total;
    else if (days <= 90) buckets["61–90 dní"] += i.total;
    else buckets["90+ dní"] += i.total;
  }
  return buckets;
}

function grossMargin(range) {
  let revenue = 0, cost = 0;
  for (const i of DATA.invoices_issued) {
    if (!inRange(i.date, range) || !i.items) continue;
    for (const it of i.items) { revenue += it.total; cost += it.qty * (it.purchase_price || 0); }
  }
  return revenue ? (revenue - cost) / revenue : 0;
}

/* ---------- charty ---------- */
let charts = [];
function destroyCharts() { charts.forEach((c) => c.destroy()); charts = []; }
function mkChart(id, cfg) {
  const el = document.getElementById(id);
  if (!el) return;
  Chart.defaults.font.family = "Inter, sans-serif";
  Chart.defaults.color = "#64748b";
  const c = new Chart(el, cfg);
  charts.push(c);
  return c;
}
const gridOpts = { grid: { color: "#f1f5f9" }, border: { display: false } };
const moneyTicks = { callback: (v) => czkShort(v) };

/* ---------- pohledy ---------- */
const views = {
  prehled: { title: "Přehled", render: renderPrehled },
  prodej: { title: "Prodej", render: renderProdej },
  pohledavky: { title: "Pohledávky & Závazky", render: renderPohledavky },
  sklad: { title: "Sklad", render: renderSklad },
  import: { title: "Napojení na Pohodu", render: renderImport },
};
let currentView = "prehled";

function kpiCard(label, value, delta, invertColors = false) {
  let deltaHtml = "";
  if (delta !== null && delta !== undefined && isFinite(delta)) {
    const up = delta >= 0;
    const good = invertColors ? !up : up;
    const cls = Math.abs(delta) < 0.005 ? "flat" : good ? "up" : "down";
    deltaHtml = `<div class="kpi-delta ${cls}">${up ? "▲" : "▼"} ${(Math.abs(delta) * 100).toLocaleString("cs-CZ", { maximumFractionDigits: 1 })} % vs. předchozí období</div>`;
  }
  return `<div class="card"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div>${deltaHtml}</div>`;
}

function renderPrehled(el) {
  const range = periodRange(period);
  const prev = prevRange(period);
  const iss = DATA.invoices_issued;

  const revenue = sum(iss.filter((i) => inRange(i.date, range)));
  const revenuePrev = prev ? sum(iss.filter((i) => inRange(i.date, prev))) : 0;
  const unpaid = iss.filter((i) => !i.paid);
  const overdue = unpaid.filter((i) => i.due_date < TODAY);
  const stockValue = sum(DATA.stock, (s) => s.value);
  const cash = sum(DATA.bank_accounts, (a) => a.currency === "EUR" ? a.balance * EUR_CZK : a.balance);
  const margin = grossMargin(range);
  const marginPrev = prev ? grossMargin(prev) : null;

  el.innerHTML = `
    <div class="grid kpi">
      ${kpiCard("Obrat (vydané faktury)", czk(revenue), revenuePrev ? revenue / revenuePrev - 1 : null)}
      ${kpiCard("Hrubá marže", (margin * 100).toLocaleString("cs-CZ", { maximumFractionDigits: 1 }) + " %", marginPrev ? margin - marginPrev : null)}
      ${kpiCard("Po splatnosti", czk(sum(overdue)), null)}
      ${kpiCard("Stav účtů + pokladna", czk(cash), null)}
      ${kpiCard("Hodnota skladu", czk(stockValue), null)}
    </div>
    <div class="grid two">
      <div class="card"><h3>Obrat po měsících</h3><div class="chart-wrap"><canvas id="chMonthly"></canvas></div></div>
      <div class="card"><h3>Kumulativní obrat — letos vs. loni</h3><div class="chart-wrap"><canvas id="chCumul"></canvas></div></div>
    </div>
    <div class="grid two">
      <div class="card"><h3>Top odběratelé</h3><div class="chart-wrap"><canvas id="chTop"></canvas></div></div>
      <div class="card"><h3>Tržby podle segmentu</h3><div class="chart-wrap"><canvas id="chSeg"></canvas></div></div>
    </div>`;

  const mon = monthly(iss, range);
  const monPrev = prev ? new Map(monthly(iss, prev).map(([ym, v]) => [ym.slice(5), v])) : null;
  mkChart("chMonthly", {
    type: "bar",
    data: {
      labels: mon.map(([ym]) => monthLabel(ym)),
      datasets: [
        { label: "Obrat", data: mon.map(([, v]) => v), backgroundColor: "#2563eb", borderRadius: 5 },
        ...(monPrev ? [{ label: "Předchozí období", data: mon.map(([ym]) => monPrev.get(ym.slice(5)) || 0), backgroundColor: "#c7d2fe", borderRadius: 5 }] : []),
      ],
    },
    options: {
      maintainAspectRatio: false,
      scales: { y: { ...gridOpts, ticks: moneyTicks }, x: { grid: { display: false }, border: { display: false } } },
      plugins: { legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12 } }, tooltip: { callbacks: { label: (c) => c.dataset.label + ": " + czk(c.raw) } } },
    },
  });

  // kumulativní běžný rok vs minulý
  const thisYear = String(new Date(TODAY).getFullYear());
  const lastYear = String(+thisYear - 1);
  const cum = (year) => {
    const m = new Map(monthly(iss, [`${year}-01-01`, `${year}-12-31`]));
    let acc = 0;
    return Array.from({ length: 12 }, (_, i) => {
      const ym = `${year}-${String(i + 1).padStart(2, "0")}`;
      if (year === thisYear && ym > TODAY.slice(0, 7)) return null;
      acc += m.get(ym) || 0;
      return acc;
    });
  };
  mkChart("chCumul", {
    type: "line",
    data: {
      labels: ["led", "úno", "bře", "dub", "kvě", "čvn", "čvc", "srp", "zář", "říj", "lis", "pro"],
      datasets: [
        { label: thisYear, data: cum(thisYear), borderColor: "#2563eb", backgroundColor: "rgba(37,99,235,.08)", fill: true, tension: .3, pointRadius: 2 },
        { label: lastYear, data: cum(lastYear), borderColor: "#94a3b8", borderDash: [5, 4], tension: .3, pointRadius: 0 },
      ],
    },
    options: {
      maintainAspectRatio: false,
      scales: { y: { ...gridOpts, ticks: moneyTicks }, x: { grid: { display: false }, border: { display: false } } },
      plugins: { legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12 } }, tooltip: { callbacks: { label: (c) => c.dataset.label + ": " + czk(c.raw) } } },
    },
  });

  const top = topBy(iss, range, "partner", 8);
  mkChart("chTop", {
    type: "bar",
    data: { labels: top.map(([p]) => p.length > 28 ? p.slice(0, 27) + "…" : p), datasets: [{ data: top.map(([, v]) => v), backgroundColor: "#2563eb", borderRadius: 5 }] },
    options: {
      indexAxis: "y", maintainAspectRatio: false,
      scales: { x: { ...gridOpts, ticks: moneyTicks }, y: { grid: { display: false }, border: { display: false } } },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => czk(c.raw) } } },
    },
  });

  const seg = topBy(iss, range, "segment", 8);
  mkChart("chSeg", {
    type: "doughnut",
    data: { labels: seg.map(([s]) => s), datasets: [{ data: seg.map(([, v]) => v), backgroundColor: ["#2563eb", "#8b5cf6", "#059669", "#d97706", "#dc2626", "#0891b2"], borderWidth: 2 }] },
    options: {
      maintainAspectRatio: false, cutout: "62%",
      plugins: { legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12 } }, tooltip: { callbacks: { label: (c) => c.label + ": " + czk(c.raw) } } },
    },
  });
}

function renderProdej(el) {
  const range = periodRange(period);
  const iss = DATA.invoices_issued.filter((i) => inRange(i.date, range));
  const cats = categorySales(range);
  const top = topBy(DATA.invoices_issued, range, "partner", 12);
  const total = sum(iss);
  const recent = [...iss].sort((a, b) => b.date < a.date ? -1 : 1).slice(0, 15);

  el.innerHTML = `
    <div class="grid kpi">
      ${kpiCard("Obrat za období", czk(total), null)}
      ${kpiCard("Počet faktur", fmtK.format(iss.length), null)}
      ${kpiCard("Průměrná faktura", czk(iss.length ? total / iss.length : 0), null)}
      ${kpiCard("Objednávky (nevyřízené)", fmtK.format(DATA.orders.filter((o) => o.status !== "vyřízená").length), null)}
    </div>
    <div class="grid two">
      <div class="card">
        <h3>Top odběratelé — podíl na obratu</h3>
        <table><thead><tr><th>Odběratel</th><th class="num">Obrat</th><th style="width:30%">Podíl</th></tr></thead>
        <tbody>${top.map(([p, v]) => `<tr><td>${p}</td><td class="num">${czk(v)}</td><td><div class="progress"><div style="width:${(v / top[0][1] * 100).toFixed(1)}%"></div></div></td></tr>`).join("")}</tbody></table>
      </div>
      <div class="card"><h3>Tržby podle kategorie zboží</h3><div class="chart-wrap tall"><canvas id="chCat"></canvas></div></div>
    </div>
    <div class="card">
      <h3>Poslední vydané faktury</h3>
      <div class="table-scroll"><table>
        <thead><tr><th>Číslo</th><th>Datum</th><th>Odběratel</th><th>Splatnost</th><th class="num">Částka</th><th>Stav</th></tr></thead>
        <tbody>${recent.map((i) => `<tr>
          <td>${i.number}</td><td>${fmtDate(i.date)}</td><td>${i.partner}</td><td>${fmtDate(i.due_date)}</td>
          <td class="num">${czk(i.total)}</td>
          <td>${i.paid ? '<span class="badge green">uhrazeno</span>' : i.due_date < TODAY ? '<span class="badge red">po splatnosti</span>' : '<span class="badge amber">čeká</span>'}</td>
        </tr>`).join("")}</tbody>
      </table></div>
    </div>`;

  mkChart("chCat", {
    type: "doughnut",
    data: { labels: cats.map(([c]) => c), datasets: [{ data: cats.map(([, v]) => v), backgroundColor: ["#2563eb", "#8b5cf6", "#059669", "#d97706", "#dc2626", "#0891b2", "#64748b"], borderWidth: 2 }] },
    options: { maintainAspectRatio: false, cutout: "62%", plugins: { legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12 } }, tooltip: { callbacks: { label: (c) => c.label + ": " + czk(c.raw) } } } },
  });
}

function renderPohledavky(el) {
  const unpaidIss = DATA.invoices_issued.filter((i) => !i.paid).sort((a, b) => a.due_date < b.due_date ? -1 : 1);
  const unpaidRcv = DATA.invoices_received.filter((i) => !i.paid).sort((a, b) => a.due_date < b.due_date ? -1 : 1);
  const buckets = agingBuckets(DATA.invoices_issued);
  const bucketsRcv = agingBuckets(DATA.invoices_received);

  el.innerHTML = `
    <div class="grid kpi">
      ${kpiCard("Pohledávky celkem", czk(sum(unpaidIss)), null)}
      ${kpiCard("— z toho po splatnosti", czk(sum(unpaidIss.filter((i) => i.due_date < TODAY))), null)}
      ${kpiCard("Závazky celkem", czk(sum(unpaidRcv)), null)}
      ${kpiCard("Saldo (pohledávky − závazky)", czk(sum(unpaidIss) - sum(unpaidRcv)), null)}
    </div>
    <div class="card"><h3>Stáří pohledávek a závazků</h3><div class="chart-wrap short"><canvas id="chAging"></canvas></div></div>
    <div class="grid half">
      <div class="card">
        <h3>Neuhrazené vydané faktury (${unpaidIss.length})</h3>
        <div class="table-scroll" style="max-height:420px;overflow-y:auto"><table>
          <thead><tr><th>Číslo</th><th>Odběratel</th><th>Splatnost</th><th class="num">Kč</th><th class="num">Dní</th></tr></thead>
          <tbody>${unpaidIss.slice(0, 60).map((i) => {
            const days = Math.floor((new Date(TODAY) - new Date(i.due_date)) / 864e5);
            return `<tr><td>${i.number}</td><td>${i.partner}</td><td>${fmtDate(i.due_date)}</td><td class="num">${czk(i.total)}</td>
              <td class="num">${days > 0 ? `<span class="badge ${days > 30 ? "red" : "amber"}">+${days}</span>` : '<span class="badge gray">' + days + "</span>"}</td></tr>`;
          }).join("")}</tbody>
        </table></div>
      </div>
      <div class="card">
        <h3>Neuhrazené přijaté faktury (${unpaidRcv.length})</h3>
        <div class="table-scroll" style="max-height:420px;overflow-y:auto"><table>
          <thead><tr><th>Číslo</th><th>Dodavatel</th><th>Splatnost</th><th class="num">Kč</th></tr></thead>
          <tbody>${unpaidRcv.slice(0, 60).map((i) => `<tr><td>${i.number}</td><td>${i.partner}</td><td>${fmtDate(i.due_date)}</td><td class="num">${czk(i.total)}</td></tr>`).join("")}</tbody>
        </table></div>
      </div>
    </div>`;

  mkChart("chAging", {
    type: "bar",
    data: {
      labels: Object.keys(buckets),
      datasets: [
        { label: "Pohledávky", data: Object.values(buckets), backgroundColor: "#2563eb", borderRadius: 5 },
        { label: "Závazky", data: Object.values(bucketsRcv), backgroundColor: "#f59e0b", borderRadius: 5 },
      ],
    },
    options: {
      maintainAspectRatio: false,
      scales: { y: { ...gridOpts, ticks: moneyTicks }, x: { grid: { display: false }, border: { display: false } } },
      plugins: { legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12 } }, tooltip: { callbacks: { label: (c) => c.dataset.label + ": " + czk(c.raw) } } },
    },
  });
}

function renderSklad(el) {
  const stock = [...DATA.stock].sort((a, b) => b.value - a.value);
  const low = stock.filter((s) => s.qty < s.min_qty);
  const byCat = new Map();
  for (const s of stock) byCat.set(s.category, (byCat.get(s.category) || 0) + s.value);
  const cats = [...byCat.entries()].sort((a, b) => b[1] - a[1]);

  el.innerHTML = `
    <div class="grid kpi">
      ${kpiCard("Hodnota skladu (nákupní ceny)", czk(sum(stock, (s) => s.value)), null)}
      ${kpiCard("Počet položek", fmtK.format(stock.length), null)}
      ${kpiCard("Pod minimem", fmtK.format(low.length), null)}
      ${kpiCard("Prodejní hodnota skladu", czk(sum(stock, (s) => s.qty * s.selling_price)), null)}
    </div>
    <div class="grid two">
      <div class="card">
        <h3>Skladové položky</h3>
        <div class="table-scroll" style="max-height:480px;overflow-y:auto"><table>
          <thead><tr><th>Kód</th><th>Název</th><th class="num">Zásoba</th><th class="num">Hodnota</th><th>Stav</th></tr></thead>
          <tbody>${stock.map((s) => `<tr><td>${s.code}</td><td>${s.name}</td>
            <td class="num">${fmtK.format(s.qty)} ${s.unit}</td><td class="num">${czk(s.value)}</td>
            <td>${s.qty < s.min_qty ? '<span class="badge red">pod minimem</span>' : '<span class="badge green">OK</span>'}</td></tr>`).join("")}</tbody>
        </table></div>
      </div>
      <div class="card"><h3>Hodnota skladu podle kategorie</h3><div class="chart-wrap tall"><canvas id="chStockCat"></canvas></div></div>
    </div>`;

  mkChart("chStockCat", {
    type: "bar",
    data: { labels: cats.map(([c]) => c), datasets: [{ data: cats.map(([, v]) => v), backgroundColor: "#8b5cf6", borderRadius: 5 }] },
    options: {
      indexAxis: "y", maintainAspectRatio: false,
      scales: { x: { ...gridOpts, ticks: moneyTicks }, y: { grid: { display: false }, border: { display: false } } },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => czk(c.raw) } } },
    },
  });
}

function renderImport(el) {
  el.innerHTML = `
    <div class="grid half">
      <div class="card">
        <h3>Vyzkoušet hned — nahrát XML export z Pohody</h3>
        <div class="dropzone" id="dropzone">
          <div style="font-size:30px;margin-bottom:8px">⇪</div>
          <strong>Přetáhněte sem XML export vydaných faktur</strong><br>
          <span class="small">Pohoda → Soubor → Datová komunikace → XML export<br>Zpracování proběhne pouze ve vašem prohlížeči — data nikam neodesíláme.</span>
          <input type="file" id="fileInput" accept=".xml" style="display:none">
        </div>
        <div id="importResult" class="small" style="margin-top:12px"></div>
      </div>
      <div class="card">
        <h3>Jak bude fungovat automatické napojení</h3>
        <div class="steps">
          <div class="step"><div><b>Nainstalujete konektor</b>Malý program na počítači / serveru, kde běží Pohoda (MDB, SQL i E1).</div></div>
          <div class="step"><div><b>Konektor se spáruje s vaším účtem</b>Jednorázový párovací kód, žádná konfigurace sítě.</div></div>
          <div class="step"><div><b>Data se synchronizují automaticky</b>Faktury, objednávky, sklad a banka — každou hodinu, šifrovaně.</div></div>
          <div class="step"><div><b>Dashboard je vždy aktuální</b>Vy i kolegové ho otevřete kdekoliv, i na mobilu.</div></div>
        </div>
        <p class="small muted" style="margin-top:14px">Konektor je ve vývoji. Demo zatím pracuje s ručním XML importem a ukázkovými daty.</p>
      </div>
    </div>`;

  const dz = document.getElementById("dropzone");
  const fi = document.getElementById("fileInput");
  dz.addEventListener("click", () => fi.click());
  dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("drag"); });
  dz.addEventListener("dragleave", () => dz.classList.remove("drag"));
  dz.addEventListener("drop", (e) => { e.preventDefault(); dz.classList.remove("drag"); if (e.dataTransfer.files[0]) importXml(e.dataTransfer.files[0]); });
  fi.addEventListener("change", () => fi.files[0] && importXml(fi.files[0]));
}

/* Best-effort parser Pohoda XML exportu vydaných faktur (schéma invoice.xsd). */
function importXml(file) {
  const out = document.getElementById("importResult");
  file.text().then((text) => {
    const doc = new DOMParser().parseFromString(text, "application/xml");
    if (doc.querySelector("parsererror")) { out.innerHTML = '<span class="badge red">Soubor není platné XML.</span>'; return; }
    const all = doc.getElementsByTagName("*");
    const headers = [...all].filter((n) => n.localName === "invoiceHeader");
    const get = (node, name) => {
      const found = [...node.getElementsByTagName("*")].find((n) => n.localName === name);
      return found ? found.textContent.trim() : null;
    };
    const parsed = [];
    for (const h of headers) {
      const invoice = h.parentNode;
      const summary = [...invoice.children].find((n) => n.localName === "invoiceSummary");
      const total = summary ? parseFloat(get(summary, "priceHighSum") || get(summary, "priceHigh") || get(summary, "priceNone") || "0") : 0;
      parsed.push({
        number: get(h, "numberRequested") || get(h, "symVar") || "?",
        date: get(h, "date") || null,
        due_date: get(h, "dateDue") || get(h, "date"),
        partner: get(h, "company") || get(h, "name") || "Neznámý",
        ico: get(h, "ico") || "",
        segment: "Import XML",
        total: total, currency: "CZK",
        paid: !!get(h, "dateOfPayment"), paid_date: get(h, "dateOfPayment"),
      });
    }
    if (!parsed.length) { out.innerHTML = '<span class="badge amber">V souboru nebyly nalezeny žádné faktury (čekám schéma invoice.xsd).</span>'; return; }
    const valid = parsed.filter((p) => p.date && p.total > 0);
    DATA.invoices_issued.push(...valid);
    DATA.meta.company = "Vaše data (XML import)";
    document.getElementById("companyChip").textContent = DATA.meta.company;
    out.innerHTML = `<span class="badge green">Naimportováno ${valid.length} faktur.</span> Přepněte na <a href="#prehled">Přehled</a> — dashboard teď počítá i s vašimi daty.`;
  });
}

/* ---------- router & init ---------- */
function setView(v) {
  currentView = v;
  document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.view === v));
  document.getElementById("viewTitle").textContent = views[v].title;
  destroyCharts();
  views[v].render(document.getElementById("content"));
}

function renderPeriodFilter() {
  const pf = document.getElementById("periodFilter");
  pf.innerHTML = PERIODS.map((p) => `<button data-p="${p.id}" class="${p.id === period ? "active" : ""}">${p.label}</button>`).join("");
  pf.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { period = b.dataset.p; renderPeriodFilter(); setView(currentView); }));
}

window.addEventListener("hashchange", () => {
  const v = location.hash.slice(1);
  if (views[v]) setView(v);
});

document.getElementById("companyChip").textContent = DATA.meta.company;
document.getElementById("lastSync").textContent = fmtDate(DATA.meta.generated);
renderPeriodFilter();
setView(views[location.hash.slice(1)] ? location.hash.slice(1) : "prehled");
