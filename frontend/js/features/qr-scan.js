(function () {
  let qr = null;
  let isRunning = false;
  let lastCode = null;
  let submitLocked = false;

  function byId(id) {
    return document.getElementById(id);
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
    hideEl(byId("confirmBox"));

    byId("modeLoad")?.classList.remove("active");
    byId("modeTake")?.classList.remove("active");

    if (byId("qty")) byId("qty").value = "1";

    hideEl(byId("confirmLocationSelectLabel"));
    hideEl(byId("confirmLocationSelectWrap"));

    const locationSelect = byId("confirmLocationSelect");
    if (locationSelect) {
      locationSelect.innerHTML = `<option value="">Lagerplatz wählen</option>`;
    }

    window.App = window.App || {};
    window.App.currentResolvedQr = null;
    window.App.currentAction = null;

    if (byId("confirmAction")) byId("confirmAction").textContent = "-";
  }

  async function loadLocationChoices(siteName) {
    const locationSelect = byId("confirmLocationSelect");

    if (!locationSelect) return;

    const site = String(siteName || "").trim().toLowerCase();
    const locations = await window.App.productsApi.listLocations(site);

    locationSelect.innerHTML =
      `<option value="">Lagerplatz wählen</option>` +
      (locations || []).map((loc) => {
        return `<option value="${loc.id}">Regal ${loc.shelf} / Fach ${loc.row}</option>`;
      }).join("");
  }

  async function fillResolved(data) {
    const user = getCurrentUser();

    const fullName =
      [user.first_name || "", user.last_name || ""].join(" ").trim() ||
      user.username ||
      "-";

    byId("confirmWorker").textContent = fullName;
    byId("confirmLager").textContent = data.site_name || "-";
    byId("confirmProductId").textContent = data.product_id ?? "-";
    byId("confirmProductName").textContent = data.product_name || "-";
    byId("confirmNcNummer").textContent = data.nc_nummer || "-";
    byId("confirmCurrentQty").textContent = String(data.quantity ?? 0);

    if (byId("confirmCategory")) byId("confirmCategory").textContent = data.category_name || "-";
    if (byId("confirmBrand")) byId("confirmBrand").textContent = data.brand_name || "-";
    if (byId("confirmLocationId")) byId("confirmLocationId").textContent = String(data.location_id ?? "-");
    if (byId("confirmShelf")) byId("confirmShelf").textContent = String(data.shelf ?? "-");
    if (byId("confirmRow")) byId("confirmRow").textContent = String(data.row ?? "-");

    byId("actionRow")?.classList.remove("hidden");
    showEl(byId("confirmBox"));

    if (!data.location_id) {
      await loadLocationChoices(data.site_name);
      showEl(byId("confirmLocationSelectLabel"));
      showEl(byId("confirmLocationSelectWrap"));
      setMessage("Kein Lagerplatz zugewiesen. Bitte Lagerplatz wählen.", "error");
    } else {
      hideEl(byId("confirmLocationSelectLabel"));
      hideEl(byId("confirmLocationSelectWrap"));
    }

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
      await fillResolved(data);
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

    showEl(box);

    if (!window.Html5Qrcode) {
      setMessage("QR Scanner Bibliothek wurde nicht geladen.", "error");
      return;
    }

    try {
      const cameras = await Html5Qrcode.getCameras();

      if (!cameras || cameras.length === 0) {
        setMessage("Keine Kamera gefunden oder Kamera-Berechtigung fehlt.", "error");
        return;
      }

      const cameraId =
        cameras.find((c) =>
          String(c.label || "").toLowerCase().includes("back") ||
          String(c.label || "").toLowerCase().includes("rear") ||
          String(c.label || "").toLowerCase().includes("environment")
        )?.id || cameras[0].id;

      if (!qr) {
        qr = new Html5Qrcode("qrReader");
      }

      await qr.start(
        cameraId,
        {
          fps: 10,
          qrbox: { width: 200, height: 200 }
        },
        handleQrDecoded,
        () => {}
      );

      isRunning = true;
      setMessage("Scanner gestartet.");
    } catch (err) {
      console.error("Scanner start error:", err);
      setMessage(err?.message || String(err) || "Scanner konnte nicht gestartet werden.", "error");
    }
  }

  async function stopScan() {
    const box = byId("qrScanBox");

    if (!qr || !isRunning) {
      hideEl(box);
      return;
    }

    try {
      await qr.stop();
      await qr.clear();
    } catch {}

    isRunning = false;
    hideEl(box);
  }

  function chooseAction(action) {
    window.App.currentAction = action;

    byId("modeLoad")?.classList.toggle("active", action === "load");
    byId("modeTake")?.classList.toggle("active", action === "take");

    byId("confirmAction").textContent =
      action === "load" ? "Einlagern" : "Entnehmen";
  }

  async function confirmAction() {
    if (submitLocked) return;

    submitLocked = true;

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

    const site = String(resolved.site_name || "").trim().toLowerCase();

    try {
      if (!resolved.location_id) {
        const selectedLocationId = Number(byId("confirmLocationSelect")?.value || 0);

        if (!selectedLocationId) {
          setMessage("Bitte Lagerplatz auswählen.", "error");
          return;
        }

        await window.App.productsApi.setProductLocation(
          site,
          resolved.product_id,
          selectedLocationId
        );

        resolved.location_id = selectedLocationId;
      }

      const payload = {
        product_id: resolved.product_id,
        quantity: qty
      };

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
    } finally {
      submitLocked = false;
    }
  }

  function initQrScan() {
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
