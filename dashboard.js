/* ============================================================
   Dashboard logic — CB2 Collateral + MCSS Clock Connection
   ============================================================ */

"use strict";

// ── Utilities ────────────────────────────────────────────────
function el(id)         { return document.getElementById(id); }
function qs(sel, root)  { return (root || document).querySelector(sel); }
function qsa(sel, root) { return [...(root || document).querySelectorAll(sel)]; }

function qualityColor(score) {
  if (score === 0)   return "var(--text-muted)";
  if (score >= 90)   return "var(--success)";
  if (score >= 70)   return "var(--accent)";
  return "var(--danger)";
}

function statusBadgeClass(status) {
  switch (status) {
    case "Complete":    return "badge-complete";
    case "In Progress": return "badge-progress";
    case "Not Started": return "badge-notstart";
    case "Pass":        return "badge-pass";
    case "Marginal":    return "badge-marginal";
    case "Failed":      return "badge-failed";
    default:            return "";
  }
}

function metricColor(val, thresholdWarn, thresholdFail, higherIsBad = true) {
  if (higherIsBad) {
    if (val >= thresholdFail) return "var(--danger)";
    if (val >= thresholdWarn) return "var(--warn)";
    return "var(--success)";
  } else {
    if (val <= thresholdFail) return "var(--danger)";
    if (val <= thresholdWarn) return "var(--warn)";
    return "var(--success)";
  }
}

// ── Tab switching ─────────────────────────────────────────────
function initTabs() {
  qsa(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      qsa(".tab-btn").forEach(b => b.classList.remove("active"));
      qsa(".page").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      el(btn.dataset.tab).classList.add("active");
    });
  });
}

// ── Chart.js defaults ────────────────────────────────────────
function chartDefaults() {
  Chart.defaults.color = "#7c8499";
  Chart.defaults.borderColor = "#2e3347";
  Chart.defaults.font.family = "'Inter','Segoe UI',system-ui,sans-serif";
  Chart.defaults.font.size = 12;
}

// ── CB2 Overview: Donut ───────────────────────────────────────
function buildCb2DonutChart() {
  const { completed, inProgress, notStarted } = CB2_DATA.summary;
  new Chart(el("cb2DonutChart"), {
    type: "doughnut",
    data: {
      labels: ["Complete", "In Progress", "Not Started"],
      datasets: [{
        data: [completed, inProgress, notStarted],
        backgroundColor: ["#2daa5f", "#1a6fc4", "#3d4255"],
        borderWidth: 2,
        borderColor: "#1c1f2b",
        hoverBorderColor: "#252836",
      }],
    },
    options: {
      cutout: "68%",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { padding: 16, boxWidth: 12, borderRadius: 6 },
        },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}` } },
      },
    },
  });
}

// ── CB2 Quality trend: dual-axis line ─────────────────────────
function buildCb2QualityChart() {
  const { labels, avgScore, defectsFound, defectsClosed } = CB2_DATA.qualityTrend;
  new Chart(el("cb2QualityChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Avg Quality Score",
          data: avgScore,
          borderColor: "#27a99e",
          backgroundColor: "rgba(39,169,158,.12)",
          fill: true,
          tension: .35,
          yAxisID: "yScore",
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: "Defects Found",
          data: defectsFound,
          borderColor: "#d63b3b",
          backgroundColor: "transparent",
          borderDash: [4, 3],
          tension: .35,
          yAxisID: "yDefects",
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: "Defects Closed",
          data: defectsClosed,
          borderColor: "#2daa5f",
          backgroundColor: "transparent",
          borderDash: [4, 3],
          tension: .35,
          yAxisID: "yDefects",
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        yScore: {
          type: "linear",
          position: "left",
          min: 0, max: 100,
          title: { display: true, text: "Score (0–100)" },
          grid: { color: "#2e3347" },
        },
        yDefects: {
          type: "linear",
          position: "right",
          min: 0,
          title: { display: true, text: "# Defects" },
          grid: { display: false },
        },
        x: { grid: { color: "#2e3347" } },
      },
      plugins: { legend: { labels: { boxWidth: 12, padding: 14 } } },
    },
  });
}

// ── CB2 Category progress cards ───────────────────────────────
function buildCategoryCards() {
  const container = el("categoryCards");
  CB2_DATA.categories.forEach(cat => {
    const total = cat.items.length;
    const done  = cat.items.filter(i => i.status === "Complete").length;
    const wip   = cat.items.filter(i => i.status === "In Progress").length;
    const ns    = cat.items.filter(i => i.status === "Not Started").length;
    const pct   = Math.round((done / total) * 100);

    const card = document.createElement("div");
    card.className = "category-card";
    card.innerHTML = `
      <div class="category-card-header">
        <span class="category-card-name">${cat.name}</span>
        <span class="category-card-count">${done}/${total}</span>
      </div>
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width:${pct}%;background:${pct>=100?"var(--success)":pct>=60?"var(--primary)":"var(--accent)"}"></div>
      </div>
      <div class="progress-stats">
        <span><span class="stat-dot" style="background:var(--success)"></span>${done} Done</span>
        <span><span class="stat-dot" style="background:var(--primary)"></span>${wip} WIP</span>
        <span><span class="stat-dot" style="background:var(--text-muted)"></span>${ns} NS</span>
      </div>
    `;
    container.appendChild(card);
  });
}

// ── CB2 Deliverable table ─────────────────────────────────────
let cb2SortCol = "id";
let cb2SortDir = 1;

function allCb2Items() {
  return CB2_DATA.categories.flatMap(c => c.items.map(i => ({ ...i, category: c.name })));
}

function renderCb2Table(items) {
  const tbody = qs("#cb2Table tbody");
  tbody.innerHTML = "";
  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:24px">No results found.</td></tr>`;
    return;
  }
  items.forEach(item => {
    const tr = document.createElement("tr");
    const qColor  = qualityColor(item.quality);
    const qWidth  = item.quality;
    tr.innerHTML = `
      <td class="td-id">${item.id}</td>
      <td>${item.name}</td>
      <td>${item.category}</td>
      <td>${item.owner}</td>
      <td><span class="badge ${statusBadgeClass(item.status)}">${item.status}</span></td>
      <td>
        <span class="quality-score">
          <span style="color:${qColor};min-width:26px;text-align:right">${item.quality || "—"}</span>
          <span class="quality-bar"><span class="quality-bar-fill" style="width:${qWidth}%;background:${qColor}"></span></span>
        </span>
      </td>
      <td style="color:var(--text-muted);font-size:12px">${item.dueDate}</td>
    `;
    tbody.appendChild(tr);
  });
  el("cb2RowCount").textContent = `${items.length} items`;
}

function filterAndSortCb2() {
  const searchVal  = el("cb2Search").value.toLowerCase();
  const statusVal  = el("cb2StatusFilter").value;
  const catVal     = el("cb2CatFilter").value;

  let items = allCb2Items().filter(i => {
    const matchSearch = !searchVal || i.name.toLowerCase().includes(searchVal) || i.id.toLowerCase().includes(searchVal) || i.owner.toLowerCase().includes(searchVal);
    const matchStatus = !statusVal || i.status === statusVal;
    const matchCat    = !catVal    || i.category === catVal;
    return matchSearch && matchStatus && matchCat;
  });

  items.sort((a, b) => {
    let va = a[cb2SortCol]; let vb = b[cb2SortCol];
    if (typeof va === "string") va = va.toLowerCase();
    if (typeof vb === "string") vb = vb.toLowerCase();
    return va < vb ? -cb2SortDir : va > vb ? cb2SortDir : 0;
  });

  renderCb2Table(items);
}

function initCb2Table() {
  // Populate category filter
  const catSel = el("cb2CatFilter");
  CB2_DATA.categories.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.name; opt.textContent = c.name;
    catSel.appendChild(opt);
  });

  el("cb2Search").addEventListener("input", filterAndSortCb2);
  el("cb2StatusFilter").addEventListener("change", filterAndSortCb2);
  el("cb2CatFilter").addEventListener("change", filterAndSortCb2);

  // Column sorting
  qsa("#cb2Table th[data-col]").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (cb2SortCol === col) cb2SortDir *= -1;
      else { cb2SortCol = col; cb2SortDir = 1; }
      qsa("#cb2Table th[data-col]").forEach(h => { h.classList.remove("sorted"); qs(".sort-icon", h).textContent = "⇅"; });
      th.classList.add("sorted");
      qs(".sort-icon", th).textContent = cb2SortDir === 1 ? "↑" : "↓";
      filterAndSortCb2();
    });
  });

  filterAndSortCb2();
}

// ── MCSS KPI cards ────────────────────────────────────────────
function buildMcssKpis() {
  const { totalConnections, passed, marginal, failed } = MCSS_DATA.summary;
  el("mcssTotal").textContent    = totalConnections;
  el("mcssPassed").textContent   = passed;
  el("mcssMarginal").textContent = marginal;
  el("mcssFailed").textContent   = failed;
  el("mcssPassRate").textContent = `${Math.round((passed / totalConnections) * 100)}%`;
}

// ── MCSS Quality trend ────────────────────────────────────────
function buildMcssQualityChart() {
  const { labels, passRate, avgSkewPs, avgJitterPs } = MCSS_DATA.qualityMetrics;
  new Chart(el("mcssQualityChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Pass Rate (%)",
          data: passRate,
          borderColor: "#2daa5f",
          backgroundColor: "rgba(45,170,95,.12)",
          fill: true,
          tension: .35,
          yAxisID: "yPct",
          pointRadius: 4, pointHoverRadius: 6,
        },
        {
          label: "Avg Skew (ps)",
          data: avgSkewPs,
          borderColor: "#e8a020",
          backgroundColor: "transparent",
          tension: .35,
          yAxisID: "yPs",
          pointRadius: 4, pointHoverRadius: 6,
        },
        {
          label: "Avg Jitter (ps)",
          data: avgJitterPs,
          borderColor: "#d63b3b",
          backgroundColor: "transparent",
          borderDash: [4, 3],
          tension: .35,
          yAxisID: "yPs",
          pointRadius: 4, pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        yPct:  { type: "linear", position: "left",  min: 0, max: 100, title: { display: true, text: "Pass (%)" }, grid: { color: "#2e3347" } },
        yPs:   { type: "linear", position: "right", min: 0,           title: { display: true, text: "ps" },        grid: { display: false } },
        x:     { grid: { color: "#2e3347" } },
      },
      plugins: { legend: { labels: { boxWidth: 12, padding: 14 } } },
    },
  });
}

// ── MCSS Skew distribution bar chart ─────────────────────────
function buildSkewDistChart() {
  const { bins, counts } = MCSS_DATA.skewDistribution;
  new Chart(el("mcssSkewChart"), {
    type: "bar",
    data: {
      labels: bins,
      datasets: [{
        label: "Connections",
        data: counts,
        backgroundColor: counts.map((_, i) =>
          i < 2 ? "rgba(45,170,95,.75)" : i < 4 ? "rgba(232,160,32,.75)" : "rgba(214,59,59,.75)"),
        borderRadius: 4,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#2e3347" } },
        x: { grid: { display: false } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

// ── MCSS Connection table ─────────────────────────────────────
let mcssSortCol = "id";
let mcssSortDir = 1;

function renderMcssTable(items) {
  const tbody = qs("#mcssTable tbody");
  tbody.innerHTML = "";
  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:24px">No results found.</td></tr>`;
    return;
  }
  items.forEach(c => {
    const tr = document.createElement("tr");
    const skewColor   = metricColor(c.skewPs,   25, 40);
    const jitterColor = metricColor(c.jitterPs,  20, 30);
    const dcColor     = metricColor(c.dutyCycleErr, 1.0, 2.0);
    tr.innerHTML = `
      <td class="td-id">${c.id}</td>
      <td style="font-size:12px">${c.src}</td>
      <td style="font-size:12px">${c.dst}</td>
      <td style="text-align:right">${c.freqMHz.toLocaleString()}</td>
      <td style="text-align:right;color:${skewColor}">${c.skewPs}</td>
      <td style="text-align:right;color:${jitterColor}">${c.jitterPs}</td>
      <td style="text-align:right;color:${dcColor}">${c.dutyCycleErr.toFixed(1)}</td>
      <td><span class="badge ${statusBadgeClass(c.status)}">${c.status}</span></td>
    `;
    tbody.appendChild(tr);
  });
  el("mcssRowCount").textContent = `${items.length} connections`;
}

function filterAndSortMcss() {
  const searchVal  = el("mcssSearch").value.toLowerCase();
  const statusVal  = el("mcssStatusFilter").value;

  let items = MCSS_DATA.connections.filter(c => {
    const matchSearch = !searchVal || c.id.toLowerCase().includes(searchVal) || c.src.toLowerCase().includes(searchVal) || c.dst.toLowerCase().includes(searchVal);
    const matchStatus = !statusVal || c.status === statusVal;
    return matchSearch && matchStatus;
  });

  items.sort((a, b) => {
    let va = a[mcssSortCol]; let vb = b[mcssSortCol];
    if (typeof va === "string") va = va.toLowerCase();
    if (typeof vb === "string") vb = vb.toLowerCase();
    return va < vb ? -mcssSortDir : va > vb ? mcssSortDir : 0;
  });

  renderMcssTable(items);
}

function initMcssTable() {
  el("mcssSearch").addEventListener("input", filterAndSortMcss);
  el("mcssStatusFilter").addEventListener("change", filterAndSortMcss);

  qsa("#mcssTable th[data-col]").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (mcssSortCol === col) mcssSortDir *= -1;
      else { mcssSortCol = col; mcssSortDir = 1; }
      qsa("#mcssTable th[data-col]").forEach(h => { h.classList.remove("sorted"); qs(".sort-icon", h).textContent = "⇅"; });
      th.classList.add("sorted");
      qs(".sort-icon", th).textContent = mcssSortDir === 1 ? "↑" : "↓";
      filterAndSortMcss();
    });
  });

  filterAndSortMcss();
}

// ── CB2 KPI cards ─────────────────────────────────────────────
function buildCb2Kpis() {
  const { totalDeliverables, completed, inProgress, notStarted } = CB2_DATA.summary;
  el("cb2Total").textContent      = totalDeliverables;
  el("cb2Completed").textContent  = completed;
  el("cb2InProgress").textContent = inProgress;
  el("cb2NotStarted").textContent = notStarted;
  el("cb2PctDone").textContent    = `${Math.round((completed / totalDeliverables) * 100)}%`;
}

// ── Last updated stamps ───────────────────────────────────────
function setLastUpdated() {
  qsa(".last-updated").forEach(el => {
    el.textContent = `Last updated: ${CB2_DATA.summary.lastUpdated}`;
  });
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  setLastUpdated();

  // CB2 page
  buildCb2Kpis();
  buildCategoryCards();
  initCb2Table();

  // MCSS page
  buildMcssKpis();
  initMcssTable();

  // Charts (guarded in case Chart.js fails to load)
  if (typeof Chart !== "undefined") {
    chartDefaults();
    buildCb2DonutChart();
    buildCb2QualityChart();
    buildMcssQualityChart();
    buildSkewDistChart();
  }
});
