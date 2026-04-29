(function () {
  async function handleManualSubmit(event) {
    event.preventDefault();

    const action = document.querySelector("#manual-action")?.value;
    const site = (document.querySelector("#manual-site")?.value || "").trim().toLowerCase();
    const productId = Number(document.querySelector("#manual-product-id")?.value || 0);
    const quantity = Number(document.querySelector("#manual-quantity")?.value || 0);
    const message = document.querySelector("#manual-message");

    if (!site || !productId || !quantity || quantity <= 0) {
      if (message) {
        message.textContent = "Bitte Site, Produkt und Menge korrekt eingeben.";
        message.className = "message error";
      }
      return;
    }

    const payload = {
      product_id: productId,
      quantity
    };

    try {
      if (action === "take") {
        await window.App.stockApi.takeMaterial(site, payload);
      } else {
        await window.App.stockApi.loadMaterial(site, payload);
      }

      if (message) {
        message.textContent = "Buchung gespeichert.";
        message.className = "message success";
      }

      await window.App.stockTableFeature?.loadCombinedStock?.();
    } catch (err) {
      if (message) {
        message.textContent = err.message || "Buchung fehlgeschlagen.";
        message.className = "message error";
      }
    }
  }

  function initManualBooking() {
    const form = document.querySelector("#manual-form");
    if (form) {
      form.addEventListener("submit", handleManualSubmit);
    }
  }

  window.App = window.App || {};
  window.App.manualBookingFeature = {
    initManualBooking
  };
})();