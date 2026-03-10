(function () {
  function logsBody() {
    return document.getElementById("logsBody");
  }

  function stockTableWrap() {
    return document.getElementById("stockTableWrap");
  }

  function logsTableWrap() {
    return document.getElementById("logsTableWrap");
  }

  function logsPager() {
    return document.getElementById("logsPager");
  }

  function logsPageInfo() {
    return document.getElementById("logsPageInfo");
  }

  const PAGE_SIZE = 50;
  let currentOffset = 0;

  function renderLogs(rows) {
    const tbody = logsBody();
    if (!tbody) return;

    tbody.innerHTML = "";

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const workerName = `${row.first_name || ""} ${row.last_name || ""}`.trim();
      const actionLabel =
        row.action === "load" ? "Einlagern" :
        row.action === "take" ? "Entnehmen" :
        row.action || "";

      tr.innerHTML = `
        <td>${row.id}</td>
        <td>${row.created_at || ""}</td>
        <td>${actionLabel}</td>
        <td>${row.product_id}</td>
        <td>${row.product_name || ""}</td>
        <td>${row.quantity}</td>
        <td>${row.lager_name || ""}</td>
        <td>${workerName}</td>
      `;
      tbody.appendChild(tr);
    });

    if (logsPageInfo()) {
      const from = rows.length ? currentOffset + 1 : 0;
      const to = currentOffset + rows.length;
      logsPageInfo().textContent = `Zeige ${from} bis ${to}`;
    }

    const prevBtn = document.getElementById("logsPrevBtn");
    const nextBtn = document.getElementById("logsNextBtn");

    if (prevBtn) prevBtn.disabled = currentOffset <= 0;
    if (nextBtn) nextBtn.disabled = rows.length < PAGE_SIZE;
  }

  async function loadLogs(offset = 0) {
    currentOffset = Math.max(0, offset);
    const rows = await window.App.historyApi.listLogs(PAGE_SIZE, currentOffset);
    renderLogs(rows || []);
  }

  function showLogsView() {
    stockTableWrap()?.classList.add("hidden");
    logsTableWrap()?.classList.remove("hidden");
    logsPager()?.classList.remove("hidden");
  }

  function hideLogsView() {
    logsTableWrap()?.classList.add("hidden");
    logsPager()?.classList.add("hidden");
    stockTableWrap()?.classList.remove("hidden");
  }

  function initLogsTable() {
    document.getElementById("logsPrevBtn")?.addEventListener("click", async () => {
      await loadLogs(Math.max(0, currentOffset - PAGE_SIZE));
    });

    document.getElementById("logsNextBtn")?.addEventListener("click", async () => {
      await loadLogs(currentOffset + PAGE_SIZE);
    });
  }

  window.App = window.App || {};
  window.App.logsTableFeature = {
    loadLogs,
    showLogsView,
    hideLogsView,
    initLogsTable
  };
})();
