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
  let manualSubmitLocked = false;

  function redirectToLogin() {
    window.location.href = "/";
  }

  function showEl(el) {
    if (!el) return;
    el.classList.remove("hidden");
    el.style.display = "block";
  }

  function hideEl(el) {
    if (!el) return;
    el.classList.add("hidden");
    el.style.display = "none";
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
    showEl(passwordModal);
    if (oldPassword) oldPassword.value = "";
    if (newPassword) newPassword.value = "";
    setPasswordMessage("");
  }

  function closePasswordModal() {
    hideEl(passwordModal);
    if (oldPassword) oldPassword.value = "";
    if (newPassword) newPassword.value = "";
    setPasswordMessage("");
  }

  function showStockView() {
    stockSearch?.classList.remove("hidden");
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

    if (currentUserName) {
      currentUserName.textContent = [first, last].join(" ").trim() || username || "-";
    }

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
    showEl(qrScanBox);
    hideEl(manualBox);

    chooseScanBtn?.classList.add("primary");
    chooseManualBtn?.classList.remove("primary");
  }

  async function showManualMode() {
    await window.App.qrScanFeature?.stopScan?.();

    hideEl(qrScanBox);
    showEl(manualBox);

    chooseManualBtn?.classList.add("primary");
    chooseScanBtn?.classList.remove("primary");

    await loadManualProductsAndLocations();
    await syncManualLocationVisibility();
  }

  chooseScanBtn?.addEventListener("click", async () => {
    showScanMode();
    await window.App.qrScanFeature?.startScan?.();
  });

  chooseManualBtn?.addEventListener("click", showManualMode);

  stockClearBtn?.addEventListener("click", async () => {
    window.App.stockTableFeature?.clearStockFilter?.();

    hideEl(stockQrScanBox);

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

    showEl(stockQrScanBox);

    if (!window.Html5Qrcode) {
      setMessage("QR Scanner Bibliothek wurde nicht geladen.", "error");
      return;
    }

    if (!stockQr) {
      stockQr = new Html5Qrcode("stockQrReader");
    }

    try {
      await stockQr.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 200, height: 200 } },
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
            hideEl(stockQrScanBox);
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
      hideEl(stockQrScanBox);
      return;
    }

    await startStockScan();
  });

  async function loadManualProductsAndLocations() {
    const site = (document.getElementById("manualStandort")?.value || "").trim().toLowerCase();
    const productSelect = document.getElementById("manualProductId");
    const locationSelect = document.getElementById("manualLocationId");

    if (!site || !productSelect || !locationSelect) return;

    const [products, locations] = await Promise.all([
      window.App.productsApi.listProducts(site),
      window.App.productsApi.listLocations(site)
    ]);

    productSelect.innerHTML =
      `<option value="">Produkt wählen</option>` +
      (products || []).map((p) => {
        const nc = p.nc_nummer ? ` | ${p.nc_nummer}` : "";
        return `<option value="${p.id}">${p.product_name}${nc}</option>`;
      }).join("");

    locationSelect.innerHTML =
      `<option value="">Lagerplatz wählen</option>` +
      (locations || []).map((loc) => {
        return `<option value="${loc.id}">Regal ${loc.shelf} / Fach ${loc.row}</option>`;
      }).join("");
  }

  async function syncManualLocationVisibility() {
    const site = (document.getElementById("manualStandort")?.value || "").trim().toLowerCase();
    const productId = Number(document.getElementById("manualProductId")?.value || 0);
    const locationLabel = document.getElementById("manualLocationLabel");
    const locationSelect = document.getElementById("manualLocationId");

    if (!site || !productId || !locationLabel || !locationSelect) {
      hideEl(locationLabel);
      hideEl(locationSelect);
      return;
    }

    try {
      const data = await window.App.productsApi.resolveProductForStandort(site, productId);

      if (data && data.location_id) {
        hideEl(locationLabel);
        hideEl(locationSelect);
        return;
      }
    } catch {}

    showEl(locationLabel);
    showEl(locationSelect);
  }

  async function handleManualConfirm() {
    if (manualSubmitLocked) return;

    manualSubmitLocked = true;

    const site = (document.getElementById("manualStandort")?.value || "").trim().toLowerCase();
    const productId = Number(document.getElementById("manualProductId")?.value || 0);
    const action = document.getElementById("manualAction")?.value;
    const quantity = Number(document.getElementById("manualQty")?.value || 0);
    const locationId = Number(document.getElementById("manualLocationId")?.value || 0);

    if (!site || !productId || !quantity || quantity <= 0) {
      setMessage("Manuelle Eingabe ist unvollständig.", "error");
      return;
    }

    try {
      const locationVisible = !document.getElementById("manualLocationId")?.classList.contains("hidden");

      if (locationVisible) {
        if (!locationId) {
          setMessage("Bitte Lagerplatz auswählen.", "error");
          return;
        }

        await window.App.productsApi.setProductLocation(site, productId, locationId);
      }

      const payload = {
        product_id: productId,
        quantity
      };

      if (action === "take") {
        await window.App.stockApi.takeMaterial(site, payload);
      } else {
        await window.App.stockApi.loadMaterial(site, payload);
      }

      setMessage("Manuelle Buchung gespeichert.", "success");

      await window.App.stockTableFeature?.loadCombinedStock?.();
      await syncManualLocationVisibility();
    } catch (err) {
      setMessage(err.message || "Manuelle Buchung fehlgeschlagen.", "error");
    } finally {
      manualSubmitLocked = false;
    }
  }

  manualConfirmBtn?.addEventListener("click", handleManualConfirm);

  document.getElementById("manualStandort")?.addEventListener("change", async () => {
    await loadManualProductsAndLocations();
    await syncManualLocationVisibility();
  });

  document.getElementById("manualProductId")?.addEventListener("change", syncManualLocationVisibility);

  manualResetBtn?.addEventListener("click", async () => {
    const manualProductId = document.getElementById("manualProductId");
    const manualQty = document.getElementById("manualQty");
    const manualAction = document.getElementById("manualAction");
    const manualStandort = document.getElementById("manualStandort");

    if (manualProductId) manualProductId.value = "";
    if (manualQty) manualQty.value = "1";
    if (manualAction) manualAction.value = "load";
    if (manualStandort) manualStandort.value = "konstanz";

    setMessage("");

    await loadManualProductsAndLocations();
    await syncManualLocationVisibility();
  });

  window.App = window.App || {};
  window.App.reloadCombinedStock = window.App.stockTableFeature?.loadCombinedStock;

  window.App.qrScanFeature?.initQrScan?.();
  window.App.stockTableFeature?.initStockTable?.();

  showScanMode();
  showStockView();

  loadManualProductsAndLocations().catch(console.error);
  window.App.stockTableFeature?.loadCombinedStock?.().catch(console.error);
})();
