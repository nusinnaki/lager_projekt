(function () {
  const { apiGet, apiPost } = window.App || {};

  const msg = document.getElementById("msg");
  const stockBody = document.getElementById("stockBody");

  const qrScanBtn = document.getElementById("qrScanBtn");
  const qrStopBtn = document.getElementById("qrStopBtn");
  const qrScanBox = document.getElementById("qrScanBox");

  const actionRow = document.getElementById("actionRow");
  const modeLoad = document.getElementById("modeLoad");
  const modeTake = document.getElementById("modeTake");

  const confirmBox = document.getElementById("confirmBox");
  const confirmWorker = document.getElementById("confirmWorker");
  const confirmAction = document.getElementById("confirmAction");
  const confirmLager = document.getElementById("confirmLager");
  const confirmProductId = document.getElementById("confirmProductId");
  const confirmProductName = document.getElementById("confirmProductName");
  const confirmNcNummer = document.getElementById("confirmNcNummer");
  const qty = document.getElementById("qty");
  const confirmBtn = document.getElementById("confirmBtn");
  const resetBtn = document.getElementById("resetBtn");

  const stockScanBtn = document.getElementById("stockScanBtn");
  const stockSearch = document.getElementById("stockSearch");
  const stockClearBtn = document.getElementById("stockClearBtn");
  const stockQrScanBox = document.getElementById("stockQrScanBox");

  const passwordModal = document.getElementById("passwordModal");
  const currentUserName = document.getElementById("currentUserName");
  const oldPassword = document.getElementById("oldPassword");
  const newPassword = document.getElementById("newPassword");
  const savePasswordBtn = document.getElementById("savePasswordBtn");
  const closePasswordBtn = document.getElementById("closePasswordBtn");
  const passwordMsg = document.getElementById("passwordMsg");

  const state = {
    action: "",
    siteKey: "",
    siteLabel: "",
    lagerId: null,
    productId: null,
    productName: "",
    ncNummer: "",
    stockRows: [],
    flowScanner: null,
    flowScannerRunning: false,
    stockScanner: null,
    stockScannerRunning: false,
    scanLocked: false
  };

  const siteMap = {
    1: { key: "konstanz", label: "Konstanz" },
    2: { key: "sindelfingen", label: "Sindelfingen" }
  };

  function getCurrentUser() {
    try {
      return JSON.parse(localStorage.getItem("lager_user") || "{}");
    } catch {
      return {};
    }
  }

  function setMsg(text) {
    if (msg) msg.textContent = text || "";
  }

  function setPasswordMsg(text) {
    if (passwordMsg) passwordMsg.textContent = text || "";
  }

  function safe(v) {
    return v == null ? "" : String(v);
  }

  function productLabel(p) {
    return safe(p.product_name) || safe(p.nc_nummer) || `Produkt ${safe(p.id || p.product_id)}`;
  }

  function currentWorkerLabel() {
    const user = getCurrentUser();
    const full = [user.first_name || "", user.last_name || ""].join(" ").trim();
    return full || user.username || "-";
  }

  function show(el) {
    if (el) el.style.display = "";
  }

  function hide(el) {
    if (el) el.style.display = "none";
  }

  function setActionButtons() {
    if (modeLoad) modeLoad.classList.toggle("active", state.action === "load");
    if (modeTake) modeTake.classList.toggle("active", state.action === "take");
  }

  async function stopFlowScan() {
    if (!state.flowScanner) {
      hide(qrScanBox);
      hide(qrStopBtn);
      state.flowScannerRunning = false;
      state.scanLocked = false;
      return;
    }

    try {
      if (state.flowScannerRunning) {
        await state.flowScanner.stop();
      }
    } catch {}

    try {
      await state.flowScanner.clear();
    } catch {}

    state.flowScanner = null;
    state.flowScannerRunning = false;
    state.scanLocked = false;
    hide(qrScanBox);
    hide(qrStopBtn);
  }

  async function stopStockScan() {
    if (!state.stockScanner) {
      hide(stockQrScanBox);
      state.stockScannerRunning = false;
      return;
    }

    try {
      if (state.stockScannerRunning) {
        await state.stockScanner.stop();
      }
    } catch {}

    try {
      await state.stockScanner.clear();
    } catch {}

    state.stockScanner = null;
    state.stockScannerRunning = false;
    hide(stockQrScanBox);
  }

  function resetFlow() {
    state.action = "";
    state.siteKey = "";
    state.siteLabel = "";
    state.lagerId = null;
    state.productId = null;
    state.productName = "";
    state.ncNummer = "";

    setActionButtons();
    hide(actionRow);
    hide(confirmBox);

    if (qty) qty.value = "1";
    setMsg("");
  }

  async function resetAll() {
    resetFlow();
    await stopFlowScan();
  }

  function fillConfirmation() {
    if (confirmWorker) confirmWorker.textContent = currentWorkerLabel();
    if (confirmAction) {
      confirmAction.textContent =
        state.action === "load" ? "Einlagern" :
        state.action === "take" ? "Entnehmen" : "-";
    }
    if (confirmLager) confirmLager.textContent = state.siteLabel || "-";
    if (confirmProductId) confirmProductId.textContent = state.productId != null ? String(state.productId) : "-";
    if (confirmProductName) confirmProductName.textContent = state.productName || "-";
    if (confirmNcNummer) confirmNcNummer.textContent = state.ncNummer || "-";
  }

  async function loadCombinedStock() {
    const rows = await apiGet("/stock/combined");
    state.stockRows = Array.isArray(rows) ? rows : [];
    renderStock();
  }

  function renderStock() {
    if (!stockBody) return;

    const q = (stockSearch && stockSearch.value ? stockSearch.value : "").toLowerCase().trim();
    stockBody.innerHTML = "";

    const filtered = state.stockRows.filter(row => {
      const label = productLabel(row);

      return (
        !q ||
        String(row.product_id).includes(q) ||
        label.toLowerCase().includes(q) ||
        safe(row.nc_nummer).toLowerCase().includes(q)
      );
    });

    filtered.sort((a, b) => Number(a.product_id) - Number(b.product_id));

    for (const row of filtered) {
      const tr = document.createElement("tr");

      const tdId = document.createElement("td");
      const tdProduct = document.createElement("td");
      const tdKonstanz = document.createElement("td");
      const tdSindelfingen = document.createElement("td");
      const tdTotal = document.createElement("td");

      tdId.textContent = String(row.product_id);
      tdProduct.textContent = productLabel(row);

      tdKonstanz.className = "right";
      tdSindelfingen.className = "right";
      tdTotal.className = "right";

      tdKonstanz.textContent = String(Number(row.qty_konstanz ?? 0));
      tdSindelfingen.textContent = String(Number(row.qty_sindelfingen ?? 0));
      tdTotal.textContent = String(Number(row.qty_total ?? 0));

      tr.appendChild(tdId);
      tr.appendChild(tdProduct);
      tr.appendChild(tdKonstanz);
      tr.appendChild(tdSindelfingen);
      tr.appendChild(tdTotal);

      stockBody.appendChild(tr);
    }
  }

  function parseQrText(raw) {
    const value = String(raw || "").trim();

    const exact = value.match(/^(\d+)-(\d+)$/);
    if (exact) {
      return {
        code: `${exact[1]}-${exact[2]}`,
        lager_id: Number(exact[1]),
        product_id: Number(exact[2])
      };
    }

    return null;
  }

  async function applyQrResult(detail) {
    if (!detail) {
      setMsg("Ungültiger QR-Code.");
      return;
    }

    const siteInfo = siteMap[Number(detail.lager_id)];
    if (!siteInfo) {
      setMsg("Unbekanntes Lager im QR-Code.");
      return;
    }

    const resolved = await apiGet(`/resolve?code=${encodeURIComponent(detail.code)}`);

    state.action = "";
    state.siteKey = siteInfo.key;
    state.siteLabel = siteInfo.label;
    state.lagerId = Number(detail.lager_id);
    state.productId = Number(resolved.product_id);
    state.productName = productLabel(resolved);
    state.ncNummer = safe(resolved.nc_nummer);

    fillConfirmation();
    setActionButtons();
    show(actionRow);
    hide(confirmBox);

    setMsg(`Scan erkannt: ${state.siteLabel}, Produkt ${state.productId}`);
  }

  async function startFlowScan() {
    if (!window.Html5Qrcode) {
      setMsg("Scanner-Bibliothek fehlt.");
      return;
    }

    await stopFlowScan();

    show(qrScanBox);
    show(qrStopBtn);
    setMsg("Scanner geöffnet.");

    state.flowScanner = new Html5Qrcode("qrReader");

    try {
      state.flowScannerRunning = true;
      state.scanLocked = false;

      await state.flowScanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 260 },
        async (decodedText) => {
          if (state.scanLocked) return;
          state.scanLocked = true;

          try {
            const parsed = parseQrText(decodedText);

            if (!parsed) {
              setMsg(`QR ungültig: ${decodedText}`);
              state.scanLocked = false;
              return;
            }

            setMsg(`QR gelesen: ${parsed.code}`);
            await applyQrResult(parsed);
            await stopFlowScan();
          } catch (err) {
            setMsg(String(err.message || err));
            state.scanLocked = false;
          }
        },
        () => {}
      );
    } catch (err) {
      state.flowScannerRunning = false;
      setMsg(String(err && err.message ? err.message : err));
      await stopFlowScan();
    }
  }

  async function startStockScan() {
    if (!window.Html5Qrcode) return;

    await stopStockScan();
    show(stockQrScanBox);

    state.stockScanner = new Html5Qrcode("stockQrReader");

    try {
      state.stockScannerRunning = true;

      await state.stockScanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 260 },
        async (decodedText) => {
          const parsed = parseQrText(decodedText);
          if (!parsed) return;

          if (stockSearch) stockSearch.value = String(parsed.product_id);
          renderStock();
          await stopStockScan();
        },
        () => {}
      );
    } catch {
      await stopStockScan();
    }
  }

  function chooseAction(action) {
    if (!state.productId || !state.siteKey) {
      setMsg("Bitte zuerst scannen.");
      return;
    }

    state.action = action;
    setActionButtons();
    fillConfirmation();
    show(confirmBox);
  }

  async function saveAction() {
    if (!state.siteKey || !state.productId) {
      setMsg("Produkt oder Lager fehlt.");
      return;
    }

    if (!state.action) {
      setMsg("Bitte Aktion wählen.");
      return;
    }

    const quantity = Number(qty && qty.value ? qty.value : 0);
    if (!quantity || quantity <= 0) {
      setMsg("Bitte gültige Menge eingeben.");
      return;
    }

    try {
      await apiPost(`/${state.siteKey}/${state.action}`, {
        product_id: state.productId,
        quantity
      });

      setMsg("Gespeichert.");
      await loadCombinedStock();
      resetFlow();
    } catch (err) {
      setMsg(String(err.message || err));
    }
  }

  async function savePassword() {
    const current_password = oldPassword ? oldPassword.value : "";
    const new_password = newPassword ? newPassword.value : "";

    if (!current_password || !new_password) {
      setPasswordMsg("Bitte beide Felder ausfüllen.");
      return;
    }

    try {
      await apiPost("/auth/change-password", {
        current_password,
        new_password
      });

      if (oldPassword) oldPassword.value = "";
      if (newPassword) newPassword.value = "";
      setPasswordMsg("Passwort geändert.");
    } catch (err) {
      setPasswordMsg(String(err.message || err));
    }
  }

  if (qrScanBtn) qrScanBtn.addEventListener("click", startFlowScan);
  if (qrStopBtn) qrStopBtn.addEventListener("click", stopFlowScan);

  if (modeLoad) modeLoad.addEventListener("click", () => chooseAction("load"));
  if (modeTake) modeTake.addEventListener("click", () => chooseAction("take"));
  if (confirmBtn) confirmBtn.addEventListener("click", saveAction);
  if (resetBtn) resetBtn.addEventListener("click", resetAll);

  if (stockSearch) stockSearch.addEventListener("input", renderStock);
  if (stockScanBtn) stockScanBtn.addEventListener("click", startStockScan);
  if (stockClearBtn) {
    stockClearBtn.addEventListener("click", async () => {
      if (stockSearch) stockSearch.value = "";
      renderStock();
      await stopStockScan();
    });
  }

  if (currentUserName) {
    currentUserName.addEventListener("click", () => {
      if (passwordModal) passwordModal.style.display = "block";
      setPasswordMsg("");
    });
  }

  if (closePasswordBtn) {
    closePasswordBtn.addEventListener("click", () => {
      if (passwordModal) passwordModal.style.display = "none";
      setPasswordMsg("");
    });
  }

  if (savePasswordBtn) savePasswordBtn.addEventListener("click", savePassword);

  resetAll();
  loadCombinedStock().catch((err) => setMsg(String(err.message || err)));
})();