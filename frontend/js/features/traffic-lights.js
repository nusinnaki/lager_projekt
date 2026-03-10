(function () {
  function getStockClass(qty) {
    const n = Number(qty || 0);

    if (n < 5) return "stock-red";
    if (n <= 10) return "stock-yellow";
    return "";
  }

  function getStockStyle(qty) {
    const cls = getStockClass(qty);

    if (cls === "stock-red") return "background:#ffd9d9;";
    if (cls === "stock-yellow") return "background:#fff3bf;";
    return "";
  }

  window.App = window.App || {};
  window.App.trafficLightsFeature = {
    getStockClass,
    getStockStyle
  };
})();
