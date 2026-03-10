(function () {
  function stockBody() {
    return document.getElementById("stockBody");
  }

  function stockSearch() {
    return document.getElementById("stockSearch");
  }

  function getTrafficStyle(qty) {
    return window.App?.trafficLightsFeature?.getStockStyle?.(qty) || "";
  }

  function renderStockRows(rows) {
    const tbody = stockBody();
    if (!tbody) return;

    tbody.innerHTML = "";

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.setAttribute("data-stock-row", "1");

      const qtyKonstanz = Number(row.qty_konstanz || 0);
      const qtySindelfingen = Number(row.qty_sindelfingen || 0);
      const qtyTotal = Number(row.qty_total || 0);

      tr.innerHTML = `
        <td>${row.product_id}</td>
        <td>${row.product_name}</td>
        <td class="right" style="${getTrafficStyle(qtyKonstanz)}">${qtyKonstanz}</td>
        <td class="right" style="${getTrafficStyle(qtySindelfingen)}">${qtySindelfingen}</td>
        <td class="right" style="${getTrafficStyle(qtyTotal)}">${qtyTotal}</td>
      `;

      tbody.appendChild(tr);
    });
  }

  async function loadCombinedStock() {
    const rows = await window.App.stockApi.listCombinedStock();
    renderStockRows(rows || []);
  }

  function filterStock() {
    const value = (stockSearch()?.value || "").trim();

    document.querySelectorAll("[data-stock-row]").forEach((row) => {
      const firstCell = row.querySelector("td");
      const productId = (firstCell?.textContent || "").trim();
      row.style.display = !value || productId === value ? "" : "none";
    });
  }

  function clearStockFilter() {
    const input = stockSearch();
    if (input) input.value = "";
    filterStock();
  }

  function setStockFilter(productId) {
    const input = stockSearch();
    if (!input) return;
    input.value = String(productId || "").trim();
    filterStock();
  }

  function initStockTable() {
    stockSearch()?.addEventListener("input", filterStock);
  }

  window.App = window.App || {};
  window.App.stockTableFeature = {
    renderStockRows,
    loadCombinedStock,
    filterStock,
    clearStockFilter,
    setStockFilter,
    initStockTable
  };
})();
