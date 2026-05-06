const state = {
  payload: null,
  view: "overview",
  filter: "",
  selectedDeliverable: "CB2",
  selectedMetric: null,
};

const statusClassMap = {
  Green: "status-Green",
  Yellow: "status-Yellow",
  Red: "status-Red",
  Gray: "status-Gray",
  Blocked: "status-Blocked",
  "At Risk": "status-AtRisk",
  "No Data": "status-NoData",
  "0p5 Ready": "status-Green",
};

const categoryOrder = ["Progress", "Quality", "Release", "Freshness"];

async function init() {
  bindEvents();
  try {
    const response = await fetch("data/latest.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Unable to load data/latest.json (${response.status})`);
    }
    state.payload = await response.json();
    render();
  } catch (error) {
    renderLoadError(error);
  }
}

function bindEvents() {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      document.querySelectorAll(".tab-button").forEach((item) => {
        const isActive = item === button;
        item.classList.toggle("is-active", isActive);
        item.setAttribute("aria-selected", String(isActive));
      });
      document.querySelectorAll(".dashboard-view").forEach((view) => {
        view.classList.toggle("is-active", view.id === `${state.view}View`);
      });
      render();
    });
  });

  document.getElementById("searchInput").addEventListener("input", (event) => {
    state.filter = event.target.value.trim().toLowerCase();
    render();
  });
}

function render() {
  if (!state.payload) {
    return;
  }
  renderHeader();
  renderDeliverableCards();
  renderCards();
  renderMatrix();
  renderInventory();
  renderBlockers();
  renderPartitions();
}

function renderDeliverableCards() {
  const summaries = ["CB2", "MCSS"].map((deliverable) => summarizeDeliverable(deliverable));
  const container = document.getElementById("deliverableCards");
  container.replaceChildren(
    ...summaries.map((summary) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `deliverable-card ${statusClass(summary.status)}`;
      button.classList.toggle("is-selected", state.selectedDeliverable === summary.deliverable);
      button.setAttribute("aria-pressed", String(state.selectedDeliverable === summary.deliverable));
      button.innerHTML = `
        <span class="deliverable-title">${escapeHtml(summary.deliverable)}</span>
        <span class="deliverable-status">${statusChip(summary.status)}</span>
        <span class="deliverable-value">${escapeHtml(String(summary.metricCount))}</span>
        <span class="deliverable-caption">metric records</span>
        <span class="deliverable-breakdown">${escapeHtml(summary.breakdown)}</span>
      `;
      button.addEventListener("click", () => {
        state.selectedDeliverable = summary.deliverable;
        state.selectedMetric = null;
        renderDeliverableCards();
      });
      return button;
    })
  );
  renderDeliverableDetails();
}

function renderDeliverableDetails() {
  const container = document.getElementById("deliverableDetails");
  const records = filterItems(allMetricRecords().filter((record) => record.deliverable === state.selectedDeliverable));
  const metricGroups = groupBy(records, (record) => record.metric);
  const selectedMetricRecords = state.selectedMetric
    ? records.filter((record) => record.metric === state.selectedMetric)
    : records;
  container.hidden = false;
  container.innerHTML = `
    <div class="section-heading compact-heading">
      <h2>${escapeHtml(state.selectedDeliverable)} Metric Details</h2>
      <span>${records.length} shown</span>
    </div>
    <div class="metric-summary-grid">
      ${Object.entries(metricGroups).sort(([first], [second]) => first.localeCompare(second)).map(([metric, metricRecords]) => {
        const status = combineUiStatuses(metricRecords.map((record) => record.status));
        return `
          <button class="metric-summary ${statusClass(status)} ${state.selectedMetric === metric ? "is-selected" : ""}" type="button" data-metric="${escapeHtml(metric)}">
            <h3>${escapeHtml(metric)}</h3>
            <div>${statusChip(status)}</div>
            <p>${metricRecords.length} records</p>
          </button>
        `;
      }).join("")}
    </div>
    <div class="section-heading compact-heading">
      <h2>${escapeHtml(state.selectedMetric || "All Metrics")} Block Breakdown</h2>
      <button id="allMetricsButton" class="text-button" type="button" ${state.selectedMetric ? "" : "disabled"}>All metrics</button>
    </div>
    <div class="table-wrap detail-table-wrap">
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Category</th>
            <th>Clock</th>
            <th>Block</th>
            <th>Metric</th>
            <th>Value</th>
            <th>Target</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          ${selectedMetricRecords.length === 0 ? `<tr><td colspan="8" class="empty-state">No matching ${escapeHtml(state.selectedDeliverable)} metric records</td></tr>` : selectedMetricRecords.map((record) => `
            <tr>
              <td>${statusChip(record.status)}</td>
              <td>${escapeHtml(record.category || "-")}</td>
              <td>${escapeHtml(record.clock || "partition")}</td>
              <td>${escapeHtml(record.partition || "-")}</td>
              <td title="${escapeHtml(record.description || "")}">${escapeHtml(record.metric)}</td>
              <td>${escapeHtml(String(record.value))}</td>
              <td>${escapeHtml(String(record.target))}</td>
              <td class="source-cell">
                <span>${escapeHtml(record.source?.system || "unknown")} / ${escapeHtml(record.source?.run_id || "-")}</span>
                <small>${escapeHtml(record.source?.uri || "-")}</small>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
  container.querySelectorAll(".metric-summary").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedMetric = button.dataset.metric;
      renderDeliverableDetails();
    });
  });
  document.getElementById("allMetricsButton").addEventListener("click", () => {
    state.selectedMetric = null;
    renderDeliverableDetails();
  });
}

function renderHeader() {
  const summary = state.payload.summary;
  document.getElementById("generatedAt").textContent = `Last updated: ${formatDate(summary.generated_at)}`;
  const finishState = document.getElementById("finishState");
  finishState.textContent = summary.finish_state;
  finishState.className = `status-pill ${statusClass(summary.finish_state)}`;
}

function renderCards() {
  const container = document.getElementById("summaryCards");
  container.replaceChildren(
    ...state.payload.cards.map((card) => {
      const element = document.createElement("article");
      element.className = "kpi-card";
      element.innerHTML = `
        <div class="kpi-label">${escapeHtml(card.label)}</div>
        <div class="kpi-value">${escapeHtml(String(card.value))}</div>
      `;
      element.classList.add(statusClass(card.status));
      return element;
    })
  );
}

function renderMatrix() {
  const rows = filterItems(state.payload.clock_partition_matrix || []);
  document.getElementById("pairCount").textContent = `${rows.length} shown`;
  const body = document.getElementById("matrixRows");
  if (rows.length === 0) {
    body.innerHTML = `<tr><td colspan="9" class="empty-state">No matching clock-partition pairs</td></tr>`;
    return;
  }

  body.replaceChildren(
    ...rows.map((rollup) => {
      const clock = rollup.metrics.find((metric) => metric.clock)?.clock || "-";
      const partition = rollup.metrics.find((metric) => metric.partition)?.partition || "-";
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${escapeHtml(clock)}</td>
        <td>${escapeHtml(partition)}</td>
        <td>${statusChip(rollup.status, rollup.finish_state)}</td>
        <td>${statusChip(rollup.deliverables?.CB2?.status || "Gray")}</td>
        <td>${statusChip(rollup.deliverables?.MCSS?.status || "Gray")}</td>
        ${categoryOrder.map((category) => `<td>${statusChip(rollup.categories?.[category]?.status || "Gray")}</td>`).join("")}
      `;
      return row;
    })
  );
}

function renderInventory() {
  const partitionsById = new Map((state.payload.partitions || []).map((partition) => [partition.entity_id, partition]));
  const inventory = filterItems(state.payload.metadata?.partition_inventory || []);
  document.getElementById("inventoryCount").textContent = `${inventory.length} shown`;
  const container = document.getElementById("inventoryGroups");
  if (inventory.length === 0) {
    container.innerHTML = `<div class="empty-state">No matching inventoried partitions</div>`;
    return;
  }

  const groups = groupBy(inventory, (partition) => partition.subfc || "unknown");
  container.replaceChildren(
    ...Object.entries(groups).sort(([first], [second]) => first.localeCompare(second)).map(([subfc, partitions]) => {
      const group = document.createElement("details");
      group.className = "subfc-group";
      const statuses = partitions.map((partition) => partitionsById.get(partition.partition)?.status || "Gray");
      const status = combineUiStatuses(statuses);
      const metricRecordCount = partitions.reduce((total, partition) => {
        return total + (partitionsById.get(partition.partition)?.metrics?.length || 0);
      }, 0);
      group.innerHTML = `
        <summary>
          <span class="subfc-title">${escapeHtml(subfc)}</span>
          <span class="subfc-count">${partitions.length} partitions</span>
          <span class="subfc-count">${metricRecordCount} metric records</span>
          ${statusChip(status)}
        </summary>
        <div class="table-wrap subfc-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Partition</th>
                <th>Metric Status</th>
                <th>Metric Records</th>
                <th>Raw Name</th>
              </tr>
            </thead>
            <tbody>
              ${partitions.map((partition) => {
                const rollup = partitionsById.get(partition.partition);
                const rawName = partition.raw_partition && partition.raw_partition !== partition.partition
                  ? partition.raw_partition
                  : "-";
                return `
                  <tr>
                    <td>${escapeHtml(partition.partition)}</td>
                    <td>${statusChip(rollup?.status || "Gray", rollup?.finish_state || "No Data")}</td>
                    <td>${escapeHtml(String(rollup?.metrics?.length || 0))}</td>
                    <td>${escapeHtml(rawName)}</td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      `;
      return group;
    })
  );
}

function renderBlockers() {
  const rows = filterItems(state.payload.blocking_issues || []);
  document.getElementById("blockerCount").textContent = `${rows.length} shown`;
  const body = document.getElementById("blockerRows");
  if (rows.length === 0) {
    body.innerHTML = `<tr><td colspan="8" class="empty-state">No matching blockers</td></tr>`;
    return;
  }

  body.replaceChildren(
    ...rows.map((issue) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${statusChip(issue.status)}</td>
        <td>${escapeHtml(issue.deliverable)}</td>
        <td>${escapeHtml(issue.clock || "partition")}</td>
        <td>${escapeHtml(issue.partition || "-")}</td>
        <td title="${escapeHtml(issue.description || "")}">${escapeHtml(issue.metric)}</td>
        <td>${escapeHtml(String(issue.value))}</td>
        <td>${escapeHtml(String(issue.target))}</td>
        <td>${escapeHtml(issue.source?.system || "unknown")} / ${escapeHtml(issue.source?.run_id || "-")}</td>
      `;
      return row;
    })
  );
}

function renderPartitions() {
  const partitions = filterItems(state.payload.partitions || []);
  document.getElementById("partitionCount").textContent = `${partitions.length} shown`;
  const container = document.getElementById("partitionPanels");
  if (partitions.length === 0) {
    container.innerHTML = `<div class="empty-state">No matching partitions</div>`;
    return;
  }

  container.replaceChildren(
    ...partitions.map((partition) => {
      const panel = document.createElement("article");
      panel.className = "detail-panel";
      const subfc = partition.metadata?.subfc || "unassigned";
      const rawPartition = partition.metadata?.raw_partition;
      const normalizationNote = rawPartition && rawPartition !== partition.entity_id
        ? `<p class="partition-note">Raw: ${escapeHtml(rawPartition)}</p>`
        : "";
      const metrics = partition.metrics.slice().sort((first, second) => {
        const statusRank = { Red: 0, Yellow: 1, Gray: 2, Green: 3 };
        return (statusRank[first.status] ?? 4) - (statusRank[second.status] ?? 4)
          || first.metric.localeCompare(second.metric);
      });
      panel.innerHTML = `
        <h3>${escapeHtml(partition.entity_id)} ${statusChip(partition.status, partition.finish_state)}</h3>
        <p class="partition-subfc">${escapeHtml(subfc)}</p>
        ${normalizationNote}
        <div class="metric-list">
          ${metrics.length === 0 ? `<div class="empty-state compact">No metric records yet</div>` : metrics.map((metric) => `
            <div class="metric-row">
              <span class="metric-name" title="${escapeHtml(metric.description || "")}">${escapeHtml(metric.metric)}</span>
              <span class="metric-value">${escapeHtml(String(metric.value))}</span>
              ${statusChip(metric.status)}
            </div>
          `).join("")}
        </div>
      `;
      return panel;
    })
  );
}

function filterItems(items) {
  if (!state.filter) {
    return items;
  }
  return items.filter((item) => JSON.stringify(item).toLowerCase().includes(state.filter));
}

function summarizeDeliverable(deliverable) {
  const records = allMetricRecords().filter((record) => record.deliverable === deliverable);
  const status = combineUiStatuses(records.map((record) => record.status));
  const counts = records.reduce((accumulator, record) => {
    accumulator[record.status] = (accumulator[record.status] || 0) + 1;
    return accumulator;
  }, {});
  return {
    deliverable,
    status,
    metricCount: records.length,
    breakdown: `R ${counts.Red || 0} / Y ${counts.Yellow || 0} / G ${counts.Green || 0} / N ${counts.Gray || 0}`,
  };
}

function allMetricRecords() {
  const seen = new Set();
  const records = [];
  for (const partition of state.payload.partitions || []) {
    for (const metric of partition.metrics || []) {
      const key = [metric.deliverable, metric.clock || "", metric.partition || "", metric.metric].join("|");
      if (!seen.has(key)) {
        seen.add(key);
        records.push(metric);
      }
    }
  }
  return records;
}

function groupBy(items, getKey) {
  return items.reduce((groups, item) => {
    const key = getKey(item);
    groups[key] = groups[key] || [];
    groups[key].push(item);
    return groups;
  }, {});
}

function combineUiStatuses(statuses) {
  if (!statuses.length) {
    return "Gray";
  }
  if (statuses.includes("Red")) {
    return "Red";
  }
  if (statuses.includes("Yellow")) {
    return "Yellow";
  }
  if (statuses.includes("Gray")) {
    return "Gray";
  }
  return "Green";
}

function statusChip(status, label = status) {
  const safeStatus = status || "Gray";
  return `<span class="status-chip ${statusClass(safeStatus)}"><span class="status-dot"></span><span class="status-label">${escapeHtml(label || safeStatus)}</span></span>`;
}

function statusClass(status) {
  return statusClassMap[status] || "status-Gray";
}

function formatDate(value) {
  if (!value) {
    return "unknown";
  }
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return value;
  }
  return date.toLocaleString();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderLoadError(error) {
  document.getElementById("generatedAt").textContent = "Last updated: data load failed";
  document.getElementById("summaryCards").innerHTML = `
    <article class="kpi-card status-Red">
      <div class="kpi-label">Data Load</div>
      <div class="kpi-value">Failed</div>
    </article>
  `;
  document.getElementById("matrixRows").innerHTML = `<tr><td colspan="9" class="empty-state">${escapeHtml(error.message)}</td></tr>`;
}

init();
