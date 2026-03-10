(function () {
  let qr = null;
  let isRunning = false;
  let lastCode = null;

  const SITE_NAMES = {
    1: "konstanz",
    2: "sindelfingen"
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function setMessage(text, type = "") {
    const msg = byId("msg");
    if (!msg) return;
    msg.textContent = text || "";
    msg.className = type ? `msg ${type}` : "msg";
  }

  function getCurrentUser() {
    try {
      return JSON.parse(localStorage.getItem("lager_user") || "{}");
    } catch {
      return {};
    }
  }

  function resetConfirm() {
    byId("actionRow")?.classList.add("hidden");
    if (byId("confirmBox")) byId("confirmBox").style.display = "none";
    byId("modeLoad")?.classList.remove("active");
    byId("modeTake")?.classList.remove("active");
    if (byId("qty")) byId("qty").value = "1";
    window.App = window.App || {};
    window.App.currentResolvedQr = null;
    window.App.currentAction = null;
  }

  function fillResolved(data) {
    const user = getCurrentUser();
    const fullName = [user.first_name || "", user.last_name || ""].join(" ").trim() || user.username || "-";

    byId("confirmWorker").textContent = fullName;
    byId("confirmLager").textContent = SITE_NAMES[data.lager_id] || String(data.lager_id);
    byId("confirmProductId").textContent = data.product_id;
    byId("confirmProductName").textContent = data.product_name || "-";
    byId("confirmNcNummer").textContent = data.nc_nummer || "-";
    byId("confirmCurrentQty").textContent = String(data.quantity ?? 0);

    byId("actionRow")?.classList.remove("hidden");
    if (byId("confirmBox")) byId("confirmBox").style.display = "block";

    window.App.currentResolvedQr = data;
    window.App.currentAction = null;
    byId("confirmAction").textContent = "-";
  }

  async function handleQrDecoded(codeText) {
    if (!codeText) return;
    if (codeText === lastCode) return;
    lastCode = codeText;

    try {
      const data = await window.App.stockApi.resolveQr(codeText);
      fillResolved(data);
      setMessage(`QR erkannt: ${codeText}`, "success");
    } catch (err) {
      setMessage(err.message || "QR konnte nicht aufgelöst werden.", "error");
    } finally {
      setTimeout(() => {
        lastCode = null;
      }, 1500);
    }
  }

  async function startScan() {
    const box = byId("qrScanBox");
    if (!box || isRunning) return;

    box.style.display = "block";

    if (!qr) {
      qr = new Html5Qrcode("qrReader");
    }

    try {
      await qr.start(
        { facingMode: "environment" },
        {
          fps: 10,
          qrbox: { width: 250, height: 250 }
        },
        handleQrDecoded,
        () => {}
      );
      isRunning = true;
      setMessage("Scanner gestartet.");
    } catch (err) {
      setMessage(err.message || "Scanner konnte nicht gestartet werden.", "error");
    }
  }

  async function stopScan() {
    const box = byId("qrScanBox");
    if (!qr || !isRunning) {
      if (box) box.style.display = "none";
      return;
    }

    try {
      await qr.stop();
      await qr.clear();
    } catch {}
    isRunning = false;
    if (box) box.style.display = "none";
  }

  function chooseAction(action) {
    window.App.currentAction = action;

    byId("modeLoad")?.classList.toggle("active", action === "load");
    byId("modeTake")?.classList.toggle("active", action === "take");
    byId("confirmAction").textContent = action === "load" ? "Einlagern" : "Entnehmen";
  }

  async function confirmAction() {
    const resolved = window.App.currentResolvedQr;
    const action = window.App.currentAction;
    const qty = Number(byId("qty")?.value || 0);

    if (!resolved) {
      setMessage("Kein QR-Datensatz vorhanden.", "error");
      return;
    }

    if (!action) {
      setMessage("Bitte zuerst Einlagern oder Entnehmen wählen.", "error");
      return;
    }

    if (!Number.isInteger(qty) || qty <= 0) {
      setMessage("Menge muss größer als 0 sein.", "error");
      return;
    }

    const site = SITE_NAMES[resolved.lager_id];
    const payload = {
      product_id: resolved.product_id,
      quantity: qty
    };

    try {
      if (action === "load") {
        await window.App.stockApi.loadMaterial(site, payload);
      } else {
        await window.App.stockApi.takeMaterial(site, payload);
      }

      setMessage("Buchung gespeichert.", "success");
      resetConfirm();
      await window.App.reloadCombinedStock?.();
    } catch (err) {
      setMessage(err.message || "Buchung fehlgeschlagen.", "error");
    }
  }

  function initQrScan() {
    byId("chooseScanBtn")?.addEventListener("click", () => {
      byId("manualBox").style.display = "none";
      startScan();
    });

    byId("chooseManualBtn")?.addEventListener("click", async () => {
      await stopScan();
      resetConfirm();
    });

    byId("modeLoad")?.addEventListener("click", () => chooseAction("load"));
    byId("modeTake")?.addEventListener("click", () => chooseAction("take"));
    byId("confirmBtn")?.addEventListener("click", confirmAction);
    byId("resetBtn")?.addEventListener("click", () => {
      resetConfirm();
      setMessage("");
    });
  }

  window.App = window.App || {};
  window.App.qrScanFeature = {
    initQrScan,
    startScan,
    stopScan,
    resetConfirm
  };
})();
