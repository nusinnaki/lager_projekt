(function () {
  function initSearch() {
    const input = document.querySelector("#search-input");
    if (!input) return;

    input.addEventListener("input", () => {
      const value = input.value.toLowerCase().trim();
      document.querySelectorAll("[data-product-row]").forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(value) ? "" : "none";
      });
    });
  }

  window.App = window.App || {};
  window.App.searchFeature = {
    initSearch
  };
})();
