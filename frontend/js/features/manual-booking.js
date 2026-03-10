(function () {
  async function handleManualSubmit(event) {
    event.preventDefault();

    const action = document.querySelector("#manual-action")?.value;
    const site = document.querySelector("#manual-site")?.value;
    const productId = Number(document.querySelector("#manual-product-id")?.value || 0);
    const quantity = Number(document.querySelector("#manual-quantity")?.value || 0);
    const message = document.querySelector("#manual-message");

    const payload = { product_id: productId, quantity };

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