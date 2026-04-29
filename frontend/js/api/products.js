(function () {
  async function listProducts(site) {
    return window.App.api.get(`/${site}/products`);
  }

  async function listLocations(site) {
    return window.App.api.get(`/${site}/locations`);
  }

  async function setProductLocation(site, productId, locationId) {
    return window.App.api.request(`/${site}/products/${productId}/location`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location_id: Number(locationId) })
    });
  }

  async function resolveProductForSite(site, productId) {
    return window.App.api.get(`/${site}/products/${productId}/resolve`);
  }

  window.App = window.App || {};
  window.App.productsApi = {
    listProducts,
    listLocations,
    setProductLocation,
    resolveProductForSite
  };
})();
