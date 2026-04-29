(function () {
  let rawStockRows = [];

  function stockBody() {
    return document.getElementById("stockBody");
  }

  function stockSearch() {
    return document.getElementById("stockSearch");
  }

  function siteFilter() {
    return document.getElementById("stockSiteFilter");
  }

  function categoryFilter() {
    return document.getElementById("stockCategoryFilter");
  }

  function getTrafficStyle(qty) {
    return window.App?.trafficLightsFeature?.getStockStyle?.(qty) || "";
  }

  function groupRows(rows) {
    const map = new Map();

    rows.forEach((row) => {
      const productId = String(row.product_name || "").trim();

      if (!map.has(productId)) {
        map.set(productId, {
          product_name: row.product_name || "",
          brand_name: row.brand_name || "",
          category_name: row.category_name || "",
          nc_nummer: row.nc_nummer || "",
          shelf: row.shelf,
          row: row.row,
          total_quantity: 0
        });
      }

      const item = map.get(productId);

      item.total_quantity += Number(row.quantity || 0);

      if (row.shelf !== null && row.shelf !== undefined) {
        item.shelf = row.shelf;
      }

      if (row.row !== null && row.row !== undefined) {
        item.row = row.row;
      }
    });

    return Array.from(map.values());
  }

  function populateFilters(rows) {
    const siteSelect = siteFilter();
    const categorySelect = categoryFilter();

    if (siteSelect) {
      const current = siteSelect.value || "all";
      const sites = new Map();

      rows.forEach((row) => {
        if (row.site_name) {
          sites.set(String(row.site_name).toLowerCase(), row.site_name);
        }
      });

      siteSelect.innerHTML =
        '<option value="all">Alle Sites</option>' +
        Array.from(sites.values())
          .sort()
          .map((name) => {
            return '<option value="' + String(name).toLowerCase() + '">' + name + '</option>';
          })
          .join("");

      siteSelect.value =
        [...siteSelect.options].some((opt) => opt.value === current)
          ? current
          : "all";
    }

    if (categorySelect) {
      const current = categorySelect.value || "all";
      const categories = new Map();

      rows.forEach((row) => {
        if (row.category_name) {
          categories.set(
            String(row.category_name).toLowerCase(),
            row.category_name
          );
        }
      });

      categorySelect.innerHTML =
        '<option value="all">Alle Kategorien</option>' +
        Array.from(categories.values())
          .sort()
          .map((name) => {
            return '<option value="' + String(name).toLowerCase() + '">' + name + '</option>';
          })
          .join("");

      categorySelect.value =
        [...categorySelect.options].some((opt) => opt.value === current)
          ? current
          : "all";
    }
  }

  function filteredRawRows() {
    const q = (stockSearch()?.value || "").trim().toLowerCase();
    const selectedSite = siteFilter()?.value || "all";
    const selectedCategory = categoryFilter()?.value || "all";

    return rawStockRows.filter((row) => {
      const siteName = String(row.site_name || "").toLowerCase();
      const categoryName = String(row.category_name || "").toLowerCase();

      const siteOk =
        selectedSite === "all" || siteName === selectedSite;

      const categoryOk =
        selectedCategory === "all" ||
        categoryName === selectedCategory;

      const searchOk =
        !q ||
        String(row.product_name || "")
          .toLowerCase()
          .includes(q) ||
        String(row.nc_nummer || "")
          .toLowerCase()
          .includes(q) ||
        String(row.category_name || "")
          .toLowerCase()
          .includes(q) ||
        String(row.brand_name || "")
          .toLowerCase()
          .includes(q);

      return siteOk && categoryOk && searchOk;
    });
  }

  function renderStockRows(rows) {
    const tbody = stockBody();
    if (!tbody) return;

    tbody.innerHTML = "";

    const selectedSite = siteFilter()?.value || "all";
    const grouped = groupRows(rows);

    const table = tbody.closest("table");

    if (table) {
      const headers = table.querySelectorAll("thead th");

      const shelfHeader = headers[4];
      const rowHeader = headers[5];

      if (shelfHeader) {
        shelfHeader.style.display =
          selectedSite === "all" ? "none" : "";
      }

      if (rowHeader) {
        rowHeader.style.display =
          selectedSite === "all" ? "none" : "";
      }
    }

    grouped.forEach((item) => {
      const tr = document.createElement("tr");
      const qty = Number(item.total_quantity || 0);

      const shelf =
        selectedSite === "all"
          ? ""
          : (item.shelf ?? "");

      const row =
        selectedSite === "all"
          ? ""
          : (item.row ?? "");

      tr.innerHTML =
        selectedSite === "all"
          ? `
            <td>${item.product_name || ""}</td>
            <td>${item.brand_name || ""}</td>
            <td>${item.category_name || ""}</td>
            <td>${item.nc_nummer || ""}</td>
            <td class="right" style="${getTrafficStyle(qty)}">
              ${qty}
            </td>
          `
          : `
            <td>${item.product_name || ""}</td>
            <td>${item.brand_name || ""}</td>
            <td>${item.category_name || ""}</td>
            <td>${item.nc_nummer || ""}</td>
            <td>${shelf}</td>
            <td>${row}</td>
            <td class="right" style="${getTrafficStyle(qty)}">
              ${qty}
            </td>
          `;

      tbody.appendChild(tr);
    });
  }

  function applyFilters() {
    renderStockRows(filteredRawRows());
  }

  async function loadCombinedStock() {
    const rows = await window.App.stockApi.listCombinedStock();

    rawStockRows = rows || [];

    populateFilters(rawStockRows);

    applyFilters();
  }

  function clearStockFilter() {
    const input = stockSearch();

    if (input) {
      input.value = "";
    }

    if (siteFilter()) {
      siteFilter().value = "all";
    }

    if (categoryFilter()) {
      categoryFilter().value = "all";
    }

    applyFilters();
  }

  function setStockFilter(productId) {
    const input = stockSearch();

    if (!input) return;

    input.value = String(productId || "").trim();

    applyFilters();
  }

  function initStockTable() {
    stockSearch()?.addEventListener("input", applyFilters);

    siteFilter()?.addEventListener("change", applyFilters);

    categoryFilter()?.addEventListener("change", applyFilters);
  }

  window.App = window.App || {};

  window.App.stockTableFeature = {
    renderStockRows,
    loadCombinedStock,
    filterStock: applyFilters,
    filterStockByExactId: setStockFilter,
    clearStockFilter,
    setStockFilter,
    initStockTable
  };
})();
