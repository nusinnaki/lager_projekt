(function () {
  async function listProducts(site) {
    return window.App.api.get(`/${site}/products`);
  }

  window.App = window.App || {};
  window.App.productsApi = {
    listProducts
  };
})();