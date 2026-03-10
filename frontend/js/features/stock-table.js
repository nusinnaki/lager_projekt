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
      tr.setAttribute("data-product-id", String(row.product_id || ""));
      tr.setAttribute("data-product-name", String(row.product_name || "").toLowerCase());

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
    const value = (stockSearch()?.value || "").trim().toLowerCase();

    document.querySelectorAll("[data-stock-row]").forEach((row) => {
      const productName = (row.getAttribute("data-product-name") || "").trim().toLowerCase();

      const matches =
        !value ||
        productName.includes(value);

      row.style.display = matches ? "" : "none";
    });
  }

  function filterStockByExactId(productId) {
    const exact = String(productId || "").trim();

    document.querySelectorAll("[data-stock-row]").forEach((row) => {
      const rowProductId = (row.getAttribute("data-product-id") || "").trim();
      row.style.display = !exact || rowProductId === exact ? "" : "none";
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
    filterStockByExactId(productId);
  }

  function initStockTable() {
    stockSearch()?.addEventListener("input", filterStock);
  }

  window.App = window.App || {};
  window.App.stockTableFeature = {
    renderStockRows,
    loadCombinedStock,
    filterStock,
    filterStockByExactId,
    clearStockFilter,
    setStockFilter,
    initStockTable
  };
})();
