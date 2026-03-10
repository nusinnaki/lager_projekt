(function () {
  const userRaw = localStorage.getItem("lager_user");
  const token = localStorage.getItem("lager_token");

  const currentUserName = document.getElementById("currentUserName");
  const logoutBtn = document.getElementById("logoutBtn");
  const adminBtn = document.getElementById("adminBtn");

  const chooseScanBtn = document.getElementById("chooseScanBtn");
  const chooseManualBtn = document.getElementById("chooseManualBtn");
  const qrScanBox = document.getElementById("qrScanBox");
  const manualBox = document.getElementById("manualBox");

  const stockClearBtn = document.getElementById("stockClearBtn");
  const stockScanBtn = document.getElementById("stockScanBtn");
  const stockQrScanBox = document.getElementById("stockQrScanBox");

  const showLogsBtn = document.getElementById("showLogsBtn");
  const showStockBtn = document.getElementById("showStockBtn");
  const stockSearch = document.getElementById("stockSearch");

  const manualConfirmBtn = document.getElementById("manualConfirmBtn");
  const manualResetBtn = document.getElementById("manualResetBtn");

  const passwordModal = document.getElementById("passwordModal");
  const oldPassword = document.getElementById("oldPassword");
  const newPassword = document.getElementById("newPassword");
  const savePasswordBtn = document.getElementById("savePasswordBtn");
  const closePasswordBtn = document.getElementById("closePasswordBtn");
  const passwordMsg = document.getElementById("passwordMsg");

  let stockQr = null;
  let stockQrRunning = false;
  let lastStockCode = null;

  function redirectToLogin() {
    window.location.href = "/";
  }

  function setMessage(text, type = "") {
    const msg = document.getElementById("msg");
    if (!msg) return;
    msg.textContent = text || "";
    msg.className = type ? `msg ${type}` : "msg";
  }

  function setPasswordMessage(text, type = "") {
    if (!passwordMsg) return;
    passwordMsg.textContent = text || "";
    passwordMsg.className = type ? `msg ${type}` : "msg";
  }

  function openPasswordModal() {
    if (passwordModal) passwordModal.style.display = "block";
    if (oldPassword) oldPassword.value = "";
    if (newPassword) newPassword.value = "";
    setPasswordMessage("");
  }

  function closePasswordModal() {
    if (passwordModal) passwordModal.style.display = "none";
    if (oldPassword) oldPassword.value = "";
    if (newPassword) newPassword.value = "";
    setPasswordMessage("");
  }

  function showLogsView() {
    window.App.logsTableFeature?.showLogsView?.();
    showLogsBtn?.classList.add("hidden");
    showStockBtn?.classList.remove("hidden");
    if (stockSearch) stockSearch.classList.add("hidden");
    stockScanBtn?.classList.add("hidden");
    stockClearBtn?.classList.add("hidden");
  }

  function showStockView() {
    window.App.logsTableFeature?.hideLogsView?.();
    showStockBtn?.classList.add("hidden");
    showLogsBtn?.classList.remove("hidden");
    if (stockSearch) stockSearch.classList.remove("hidden");
    stockScanBtn?.classList.remove("hidden");
    stockClearBtn?.classList.remove("hidden");
  }

  if (!token || !userRaw) {
    redirectToLogin();
    return;
  }

  try {
    const currentUser = JSON.parse(userRaw);
    const first = currentUser.first_name || "";
    const last = currentUser.last_name || "";
    const username = currentUser.username || "";
    currentUserName.textContent = [first, last].join(" ").trim() || username || "-";

    if (currentUser.is_admin && adminBtn) {
      adminBtn.classList.remove("hidden");
    }
  } catch {
    redirectToLogin();
    return;
  }

  currentUserName?.addEventListener("click", openPasswordModal);

  savePasswordBtn?.addEventListener("click", async () => {
    const current_password = oldPassword?.value || "";
    const new_password = newPassword?.value || "";

    if (!current_password) {
      setPasswordMessage("Altes Passwort fehlt.", "error");
      return;
    }

    if (!new_password || new_password.length < 8) {
      setPasswordMessage("Neues Passwort muss mindestens 8 Zeichen haben.", "error");
      return;
    }

    try {
      await window.App.authApi.changePassword(current_password, new_password);
      setPasswordMessage("Passwort erfolgreich geändert.", "success");
      setTimeout(closePasswordModal, 800);
    } catch (err) {
      setPasswordMessage(err.message || "Passwort konnte nicht geändert werden.", "error");
    }
  });

  closePasswordBtn?.addEventListener("click", closePasswordModal);

  passwordModal?.addEventListener("click", (e) => {
    if (e.target === passwordModal) closePasswordModal();
  });

  adminBtn?.addEventListener("click", () => {
    window.location.href = "/admin";
  });

  logoutBtn?.addEventListener("click", () => {
    localStorage.removeItem("lager_token");
    localStorage.removeItem("lager_user");
    redirectToLogin();
  });

  function showScanMode() {
    if (qrScanBox) qrScanBox.style.display = "block";
    if (manualBox) manualBox.style.display = "none";
    chooseScanBtn?.classList.add("primary");
    chooseManualBtn?.classList.remove("primary");
  }

  async function showManualMode() {
    await window.App.qrScanFeature?.stopScan?.();
    if (qrScanBox) qrScanBox.style.display = "none";
    if (manualBox) manualBox.style.display = "block";
    chooseManualBtn?.classList.add("primary");
    chooseScanBtn?.classList.remove("primary");
  }

  chooseScanBtn?.addEventListener("click", showScanMode);
  chooseManualBtn?.addEventListener("click", showManualMode);

  showLogsBtn?.addEventListener("click", async () => {
    try {
      await window.App.logsTableFeature.loadLogs(0);
      showLogsView();
      setMessage("");
    } catch (err) {
      setMessage(err.message || "Logs konnten nicht geladen werden.", "error");
    }
  });

  showStockBtn?.addEventListener("click", () => {
    showStockView();
    setMessage("");
  });

  stockClearBtn?.addEventListener("click", async () => {
    window.App.stockTableFeature?.clearStockFilter?.();
    if (stockQrScanBox) stockQrScanBox.style.display = "none";
    if (stockQr && stockQrRunning) {
      try {
        await stockQr.stop();
        await stockQr.clear();
      } catch {}
      stockQrRunning = false;
    }
  });

  async function startStockScan() {
    if (!stockQrScanBox || stockQrRunning) return;

    stockQrScanBox.style.display = "block";

    if (!stockQr) {
      stockQr = new Html5Qrcode("stockQrReader");
    }

    try {
      await stockQr.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        async (decodedText) => {
          if (!decodedText) return;
          if (decodedText === lastStockCode) return;
          lastStockCode = decodedText;

          try {
            const parts = String(decodedText).trim().split("-");
            if (parts.length !== 2) {
              setMessage("QR Format ungültig.", "error");
              return;
            }

            const productId = parts[1].trim();
            window.App.stockTableFeature?.setStockFilter?.(productId);
            setMessage(`Produkt-ID ${productId} gefiltert.`, "success");

            try {
              await stockQr.stop();
              await stockQr.clear();
            } catch {}
            stockQrRunning = false;
            stockQrScanBox.style.display = "none";
          } finally {
            setTimeout(() => {
              lastStockCode = null;
            }, 1500);
          }
        },
        () => {}
      );

      stockQrRunning = true;
      setMessage("Bestand-Scanner gestartet.");
    } catch (err) {
      setMessage(err.message || "Bestand-Scanner konnte nicht gestartet werden.", "error");
    }
  }

  stockScanBtn?.addEventListener("click", async () => {
    if (stockQrRunning) {
      try {
        await stockQr.stop();
        await stockQr.clear();
      } catch {}
      stockQrRunning = false;
      if (stockQrScanBox) stockQrScanBox.style.display = "none";
      return;
    }

    await startStockScan();
  });

  async function handleManualConfirm() {
    const site = document.getElementById("manualSite")?.value;
    const productId = Number(document.getElementById("manualProductId")?.value || 0);
    const action = document.getElementById("manualAction")?.value;
    const quantity = Number(document.getElementById("manualQty")?.value || 0);

    if (!site || !productId || !quantity || quantity <= 0) {
      setMessage("Manuelle Eingabe ist unvollständig.", "error");
      return;
    }

    const payload = { product_id: productId, quantity };

    try {
      if (action === "take") {
        await window.App.stockApi.takeMaterial(site, payload);
      } else {
        await window.App.stockApi.loadMaterial(site, payload);
      }

      setMessage("Manuelle Buchung gespeichert.", "success");
      await window.App.stockTableFeature?.loadCombinedStock?.();
    } catch (err) {
      setMessage(err.message || "Manuelle Buchung fehlgeschlagen.", "error");
    }
  }

  manualConfirmBtn?.addEventListener("click", handleManualConfirm);

  manualResetBtn?.addEventListener("click", () => {
    document.getElementById("manualProductId").value = "";
    document.getElementById("manualQty").value = "1";
    document.getElementById("manualAction").value = "load";
    document.getElementById("manualSite").value = "konstanz";
    setMessage("");
  });

  window.App = window.App || {};
  window.App.reloadCombinedStock = window.App.stockTableFeature?.loadCombinedStock;

  window.App.qrScanFeature?.initQrScan?.();
  window.App.stockTableFeature?.initStockTable?.();
  window.App.logsTableFeature?.initLogsTable?.();

  showScanMode();
  showStockView();
  window.App.stockTableFeature?.loadCombinedStock?.().catch(console.error);
})();
