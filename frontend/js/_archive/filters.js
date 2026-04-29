(function () {
  function initFilters() {
    const category = document.querySelector("#filter-category");
    if (!category) return;

    category.addEventListener("change", () => {
      console.log("Filter placeholder:", category.value);
    });
  }

  window.App = window.App || {};
  window.App.filtersFeature = {
    initFilters
  };
})();
