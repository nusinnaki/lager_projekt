(function () {
  function initProductDetails() {
    document.addEventListener("click", (event) => {
      const row = event.target.closest("[data-product-row]");
      if (!row) return;
      console.log("Product details placeholder");
    });
  }

  window.App = window.App || {};
  window.App.productDetailsFeature = {
    initProductDetails
  };
})();
