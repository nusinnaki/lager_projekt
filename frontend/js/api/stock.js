(function () {
  async function listStock(site) {
    return window.App.api.get(`/${site}/stock`);
  }

  async function listCombinedStock() {
    return window.App.api.get("/stock/combined");
  }

  async function takeMaterial(site, payload) {
    return window.App.api.post(`/${site}/take`, payload);
  }

  async function loadMaterial(site, payload) {
    return window.App.api.post(`/${site}/load`, payload);
  }

  async function resolveQr(code) {
    return window.App.api.get(`/resolve?code=${encodeURIComponent(code)}`);
  }

  window.App = window.App || {};
  window.App.stockApi = {
    listStock,
    listCombinedStock,
    takeMaterial,
    loadMaterial,
    resolveQr
  };
})();
