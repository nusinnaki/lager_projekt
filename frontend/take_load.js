(function () {
  const { SITE, apiGet, apiPost } = window.App || {};

  const title = document.getElementById("title");
  const workerSelect = document.getElementById("workerSelect");
  const productSelect = document.getElementById("productSelect");
  const qty = document.getElementById("qty");
  const msg = document.getElementById("msg");
  const stockBody = document.getElementById("stockBody");

  const takeBtn = document.getElementById("takeBtn");
  const loadBtn = document.getElementById("loadBtn");
  const refreshBtn = document.getElementById("refreshBtn");

  const modeSelectRow = document.getElementById("modeSelectRow");
  const modeTitleRow = document.getElementById("modeTitleRow");
  const modeTitle = document.getElementById("modeTitle");
  const modeBack = document.getElementById("modeBack");

  const modeLoad = document.getElementById("modeLoad");
  const modeTake = document.getElementById("modeTake");
  const actionBody = document.getElementById("actionBody");

  let currentMode = ""; // "load" or "take"

  function setMsg(t) { if (msg) msg.textContent = t || ""; }

  function selectedText(sel) {
    const opt = sel && sel.options ? sel.options[sel.selectedIndex] : null;
    return opt ? (opt.textContent || "").trim() : "";
  }

  function showModeSelect() {
    currentMode = "";
    if (modeSelectRow) modeSelectRow.style.display = "flex";
    if (modeTitleRow) modeTitleRow.style.display = "none";
    if (actionBody) actionBody.style.display = "none";
    if (loadBtn) loadBtn.style.display = "none";
    if (takeBtn) takeBtn.style.display = "none";
    setMsg("");
  }

  function setMode(mode) {
    currentMode = mode;

    if (modeSelectRow) modeSelectRow.style.display = "none";
    if (modeTitleRow) modeTitleRow.style.display = "flex";
    if (actionBody) actionBody.style.display = "block";

    if (modeTitle) modeTitle.textContent = mode.toUpperCase();

    if (loadBtn) loadBtn.style.display = (mode === "load") ? "inline-block" : "none";
    if (takeBtn) takeBtn.style.display = (mode === "take") ? "inline-block" : "none";

    setMsg("");
  }

  async function loadWorkers() {
    const workers = await apiGet("/workers");
    workerSelect.innerHTML = `<option value="" selected disabled>Select worker</option>`;
    for (const w of workers) {
      if (!w.active) continue;
      const opt = document.createElement("option");
      opt.value = String(w.id);
      opt.textContent = w.name;
      workerSelect.appendChild(opt);
    }
  }

  async function loadProducts() {
    const products = await apiGet("/products");
    productSelect.innerHTML = `<option value="" selected disabled>Select product</option>`;
    for (const p of products) {
      if (!p.active) continue;
      const opt = document.createElement("option");
      opt.value = String(p.id);
      opt.textContent = p.materialkurztext || p.product_name || p.name || String(p.id);
      productSelect.appendChild(opt);
    }
  }

  async function loadStock() {
    const stock = await apiGet("/stock");
    stockBody.innerHTML = "";
    for (const row of stock) {
      if (row.active === 0) continue;
      const tr = document.createElement("tr");
      const tdName = document.createElement("td");
      const tdQty = document.createElement("td");
      tdQty.className = "right";

      tdName.textContent = row.materialkurztext || row.product_name || row.name || "";
      tdQty.textContent = String(row.quantity ?? 0);

      tr.appendChild(tdName);
      tr.appendChild(tdQty);
      stockBody.appendChild(tr);
    }
  }

  async function refreshAll() {
    setMsg("");
    await loadWorkers();
    await loadProducts();
    await loadStock();
  }

  async function submitCurrentMode() {
    setMsg("");

    if (!currentMode) {
      setMsg("Select LOAD or TAKE first");
      return;
    }

    const worker_id = Number(workerSelect.value || 0);
    const product_id = Number(productSelect.value || 0);
    const quantity = Number(qty.value || 0);

    if (!worker_id || !product_id || !quantity || quantity <= 0) {
      setMsg("Missing worker, product, or quantity");
      return;
    }

    const workerName = selectedText(workerSelect);
    const productName = selectedText(productSelect);
    const actionLabel = currentMode.toUpperCase();

    if (!confirm(`${actionLabel} ${quantity}\nWorker: ${workerName}\nProduct: ${productName}\n\nConfirm?`)) return;

    await apiPost(`/${currentMode}`, { worker_id, product_id, quantity });
    setMsg("Saved");
    await loadStock();
  }

  if (!SITE) {
    if (title) title.textContent = "Invalid site";
    setMsg("Missing ?site=konstanz or ?site=sindelfingen");
    return;
  }

  if (title) title.textContent = `Lager: ${SITE}`;

  if (modeLoad) modeLoad.addEventListener("click", () => setMode("load"));
  if (modeTake) modeTake.addEventListener("click", () => setMode("take"));
  if (modeBack) modeBack.addEventListener("click", showModeSelect);

  if (takeBtn) takeBtn.addEventListener("click", submitCurrentMode);
  if (loadBtn) loadBtn.addEventListener("click", submitCurrentMode);
  if (refreshBtn) refreshBtn.addEventListener("click", refreshAll);

  showModeSelect();
  refreshAll().catch((e) => setMsg(String(e.message || e)));
})();
