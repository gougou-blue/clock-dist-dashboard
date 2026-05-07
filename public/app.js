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
const mcssStatusLabels = {
  Green: "Available",
  Yellow: "At Risk",
  Red: "Missing",
  Gray: "No Data",
};
const cb2StatusLabels = {
  Green: "Passing",
  Yellow: "Review",
  Red: "Failing",
  Gray: "No Data",
};

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
  renderCb2Checklists();
  renderCb2PostPushRuns();
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
        <span class="deliverable-status">${statusChip(summary.status, summary.statusLabel)}</span>
        <span class="deliverable-value">${escapeHtml(String(summary.value))}</span>
        <span class="deliverable-caption">${escapeHtml(summary.caption)}</span>
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
  const isMcss = state.selectedDeliverable === "MCSS";
  const isCb2 = state.selectedDeliverable === "CB2";
  const viewCopy = deliverableViewCopy(state.selectedDeliverable, records);
  const metricGroups = groupBy(records, (record) => record.metric);
  const selectedMetricRecords = state.selectedMetric
    ? records.filter((record) => record.metric === state.selectedMetric)
    : records;
  container.hidden = false;
  container.innerHTML = `
    <div class="section-heading compact-heading">
      <h2>${escapeHtml(viewCopy.title)}</h2>
      <span>${escapeHtml(viewCopy.countLabel)}</span>
    </div>
    <div class="metric-summary-grid">
      ${Object.entries(metricGroups).sort(([first], [second]) => first.localeCompare(second)).map(([metric, metricRecords]) => {
        const counts = countStatuses(metricRecords);
        const summary = summarizeCoverage(counts, isMcss ? "Available" : isCb2 ? "Passing" : "Green");
        const countLabel = isMcss
          ? `${uniqueCount(metricRecords.map((record) => record.partition))} partitions`
          : isCb2
            ? cb2MetricCountLabel(metricRecords)
            : `${metricRecords.length} total`;
        const labels = isMcss ? mcssStatusLabels : isCb2 ? cb2StatusLabels : undefined;
        return `
          <button class="metric-summary ${statusClass(summary.status)} ${state.selectedMetric === metric ? "is-selected" : ""}" type="button" data-metric="${escapeHtml(metric)}">
            <h3>${escapeHtml(metricLabel(metric))}</h3>
            <div class="metric-summary-topline">${statusChip(summary.status, summary.statusLabel)}<span>${escapeHtml(countLabel)}</span></div>
            <div class="metric-status-breakdown">${statusCountPills(counts, labels)}</div>
          </button>
        `;
      }).join("")}
    </div>
    <div class="section-heading compact-heading">
      <h2>${escapeHtml(selectedMetricTitle(state.selectedMetric, state.selectedDeliverable))}</h2>
      <button id="allMetricsButton" class="text-button" type="button" ${state.selectedMetric ? "" : "disabled"}>All metrics</button>
    </div>
    <div class="table-wrap detail-table-wrap">
      <table>
        <thead>
          ${metricDetailHeader(state.selectedDeliverable)}
        </thead>
        <tbody>
          ${selectedMetricRecords.length === 0
            ? `<tr><td colspan="${isMcss || isCb2 ? 6 : 8}" class="empty-state">No matching ${escapeHtml(state.selectedDeliverable)} records</td></tr>`
            : selectedMetricRecords.map((record) => metricDetailRow(record, state.selectedDeliverable)).join("")}
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

function renderCb2Checklists() {
  const rows = filterItems(state.payload.cb2_hierarchies || []);
  document.getElementById("cb2ChecklistCount").textContent = `${rows.length} hierarchies shown`;
  const body = document.getElementById("cb2ChecklistRows");
  if (rows.length === 0) {
    body.innerHTML = `<tr><td colspan="6" class="empty-state">No matching CB2 hierarchy checklists</td></tr>`;
    return;
  }

  body.replaceChildren(
    ...rows.map((rollup) => {
      const counts = countStatuses(rollup.metrics || []);
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${escapeHtml(rollup.entity_id)}</td>
        <td>Pre-Push</td>
        <td>${statusChip(rollup.status, checklistStatusLabel(rollup.status))}</td>
        <td>${escapeHtml(String(counts.Green || 0))}</td>
        <td>${escapeHtml(String(counts.Red || 0))}</td>
        <td>${escapeHtml(String((rollup.metrics || []).length))}</td>
      `;
      return row;
    })
  );
}

function renderCb2PostPushRuns() {
  const rows = filterItems(allMetricRecords().filter((record) => record.deliverable === "CB2" && record.checklist === "post_push"));
  const definitions = filterItems(cb2ChecklistDefinitions("post_push"));
  document.getElementById("cb2PostPushCount").textContent = rows.length
    ? `${uniqueCount(rows.map((record) => record.partition))} partitions shown`
    : `${definitions.length} checks defined / 0 partitions loaded`;
  const body = document.getElementById("cb2PostPushRows");
  if (rows.length === 0) {
    body.replaceChildren(
      ...definitions.map((definition) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>archive runs</td>
          <td>${statusChip("Gray", "No Data")}</td>
          <td title="${escapeHtml(definition.description || "")}">${escapeHtml(definition.label)}</td>
          <td>-</td>
          <td>-</td>
          <td class="source-cell">
            <span>partition archive runs</span>
            <small>${escapeHtml(definition.metric)}</small>
          </td>
        `;
        return row;
      })
    );
    return;
  }

  body.replaceChildren(
    ...rows.map((record) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${escapeHtml(record.partition || "-")}</td>
        <td>${statusChip(record.status, checklistStatusLabel(record.status))}</td>
        <td title="${escapeHtml(record.description || metricDescription(record.metric))}">${escapeHtml(metricLabel(record.metric))}</td>
        <td>${escapeHtml(String(record.value))}</td>
        <td>${escapeHtml(record.source?.run_id || "-")}</td>
        <td class="source-cell">
          <span>${escapeHtml(record.source?.system || "unknown")}</span>
          <small>${escapeHtml(record.source?.uri || "-")}</small>
        </td>
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
        <td>${escapeHtml(issue.hierarchy || issue.clock || "partition")}</td>
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
  if (deliverable === "CB2") {
    return summarizeCb2Deliverable(records);
  }
  if (deliverable === "MCSS") {
    return summarizeMcssDeliverable(records);
  }

  const counts = countStatuses(records);
  const summary = summarizeCoverage(counts);
  return {
    deliverable,
    status: summary.status,
    statusLabel: summary.statusLabel,
    value: records.length,
    caption: "metric records",
    breakdown: `G ${counts.Green || 0} / Y ${counts.Yellow || 0} / R ${counts.Red || 0} / N ${counts.Gray || 0}`,
  };
}

function summarizeCb2Deliverable(records) {
  const counts = countStatuses(records);
  const summary = summarizeCoverage(counts, "Passing");
  const postPushPartitions = uniqueCount(
    records.filter((record) => record.checklist === "post_push").map((record) => record.partition)
  );
  const passing = counts.Green || 0;
  const total = records.length;
  return {
    deliverable: "CB2",
    status: summary.status,
    statusLabel: summary.statusLabel,
    value: `${passing}/${total}`,
    caption: "pre-push checks",
    breakdown: `Passing ${counts.Green || 0} / Failing ${counts.Red || 0} / Post-push partitions ${postPushPartitions}`,
  };
}

function summarizeMcssDeliverable(records) {
  const releaseRecords = records.filter((record) => record.metric === "mcss_release_status");
  const releaseCounts = countStatuses(releaseRecords);
  const collateralCounts = countStatuses(records);
  const summary = summarizeCoverage(releaseCounts, "Available");
  const released = releaseCounts.Green || 0;
  const total = releaseRecords.length;
  return {
    deliverable: "MCSS",
    status: summary.status,
    statusLabel: summary.statusLabel,
    value: `${released}/${total}`,
    caption: "collateral coverage",
    breakdown: `Available ${collateralCounts.Green || 0} / Missing ${collateralCounts.Red || 0}`,
  };
}

function deliverableViewCopy(deliverable, records) {
  if (deliverable === "CB2") {
    return {
      title: "CB2 Checklists",
      countLabel: `${uniqueCount(records.filter((record) => record.checklist === "pre_push").map((record) => record.hierarchy))} pre-push hierarchies / ${uniqueCount(records.filter((record) => record.checklist === "post_push").map((record) => record.partition))} post-push partitions`,
    };
  }
  if (deliverable === "MCSS") {
    return {
      title: "MCSS Collateral By Partition",
      countLabel: `${uniqueCount(records.map((record) => record.partition))} partitions shown`,
    };
  }
  return {
    title: `${deliverable} Metric Details`,
    countLabel: `${records.length} shown`,
  };
}

function selectedMetricTitle(metric, deliverable) {
  if (deliverable === "CB2") {
    return metric || "All Pre-Push Checks";
  }
  if (deliverable === "MCSS") {
    return metric || "All Collateral Gates";
  }
  return `${metric || "All Metrics"} Block Breakdown`;
}

function metricDetailHeader(deliverable) {
  if (deliverable === "CB2") {
    return `
      <tr>
        <th>Status</th>
        <th>Hierarchy / Partition</th>
        <th>Checklist</th>
        <th>Checker</th>
        <th>Value</th>
        <th>Source</th>
      </tr>
    `;
  }
  if (deliverable === "MCSS") {
    return `
      <tr>
        <th>Status</th>
        <th>SubFC</th>
        <th>Partition</th>
        <th>Collateral Gate</th>
        <th>Value</th>
        <th>Source</th>
      </tr>
    `;
  }
  return `
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
  `;
}

function metricDetailRow(record, deliverable) {
  if (deliverable === "CB2") {
    return `
      <tr>
        <td>${statusChip(record.status, checklistStatusLabel(record.status))}</td>
        <td>${escapeHtml(record.hierarchy || record.partition || "-")}</td>
        <td>${escapeHtml(checklistLabel(record.checklist))}</td>
        <td title="${escapeHtml(record.description || metricDescription(record.metric))}">${escapeHtml(metricLabel(record.metric))}</td>
        <td>${escapeHtml(String(record.value))}</td>
        <td class="source-cell">
          <span>${escapeHtml(record.source?.system || "unknown")} / ${escapeHtml(record.source?.run_id || "-")}</span>
          <small>${escapeHtml(record.source?.uri || "-")}</small>
        </td>
      </tr>
    `;
  }
  if (deliverable === "MCSS") {
    return `
      <tr>
        <td>${statusChip(record.status, mcssStatusLabel(record.status))}</td>
        <td>${escapeHtml(partitionSubfc(record.partition))}</td>
        <td>${escapeHtml(record.partition || "-")}</td>
        <td title="${escapeHtml(record.description || "")}">${escapeHtml(record.metric)}</td>
        <td>${escapeHtml(String(record.value))}</td>
        <td class="source-cell">
          <span>${escapeHtml(record.source?.system || "unknown")} / ${escapeHtml(record.source?.run_id || "-")}</span>
          <small>${escapeHtml(record.source?.uri || "-")}</small>
        </td>
      </tr>
    `;
  }
  return `
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
  `;
}

function partitionSubfc(partition) {
  const item = (state.payload.metadata?.partition_inventory || []).find((entry) => entry.partition === partition);
  return item?.subfc || "-";
}

function cb2ChecklistDefinitions(checklist) {
  return state.payload.metadata?.cb2_checklists?.[checklist] || [];
}

function cb2ChecklistItems() {
  const checklists = state.payload.metadata?.cb2_checklists || {};
  return [...(checklists.pre_push || []), ...(checklists.post_push || [])];
}

function metricLabel(metric) {
  const item = cb2ChecklistItems().find((definition) => definition.metric === metric);
  return item?.label || metric;
}

function metricDescription(metric) {
  const item = cb2ChecklistItems().find((definition) => definition.metric === metric);
  return item?.description || "";
}

function mcssStatusLabel(status) {
  return mcssStatusLabels[status] || status || "No Data";
}

function checklistStatusLabel(status) {
  return cb2StatusLabels[status] || status || "No Data";
}

function checklistLabel(checklist) {
  if (checklist === "pre_push") {
    return "Pre-Push";
  }
  if (checklist === "post_push") {
    return "Post-Push";
  }
  return "-";
}

function cb2MetricCountLabel(records) {
  if (records.some((record) => record.checklist === "post_push")) {
    return `${uniqueCount(records.map((record) => record.partition))} partitions`;
  }
  return `${uniqueCount(records.map((record) => record.hierarchy))} hierarchies`;
}

function countStatuses(records) {
  return records.reduce((accumulator, record) => {
    accumulator[record.status] = (accumulator[record.status] || 0) + 1;
    return accumulator;
  }, {});
}

function statusCountPills(counts, labels = {}) {
  return ["Green", "Yellow", "Red", "Gray"]
    .filter((status) => counts[status])
    .map((status) => `<span class="status-count ${statusClass(status)}">${escapeHtml(labels[status] || status)} ${escapeHtml(String(counts[status]))}</span>`)
    .join("");
}

function uniqueCount(values) {
  return new Set(values.filter(Boolean)).size;
}

function summarizeCoverage(counts, positiveLabel = "Green") {
  const total = ["Green", "Yellow", "Red", "Gray"].reduce((sum, status) => sum + (counts[status] || 0), 0);
  if (!total) {
    return { status: "Gray", statusLabel: "No Data" };
  }

  const greenCount = counts.Green || 0;
  const greenPercent = Math.round((greenCount / total) * 100);
  if (greenCount === total) {
    return { status: "Green", statusLabel: `100% ${positiveLabel}` };
  }
  if (greenPercent >= 80) {
    return { status: "Yellow", statusLabel: `${greenPercent}% ${positiveLabel}` };
  }
  return { status: "Red", statusLabel: `${greenPercent}% ${positiveLabel}` };
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
  for (const hierarchy of state.payload.cb2_hierarchies || []) {
    for (const metric of hierarchy.metrics || []) {
      const key = [metric.deliverable, metric.hierarchy || "", metric.metric].join("|");
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
