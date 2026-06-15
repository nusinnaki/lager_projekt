(function () {
  async function listWorkers() {
    return window.App.api.get("/admin/workers");
  }

  async function createWorker(payload) {
    return window.App.api.post("/admin/workers", payload);
  }

  async function updateWorker(workerId, payload) {
    return window.App.api.request(`/admin/workers/${workerId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  async function listProducts() {
    return window.App.api.get("/admin/products");
  }

  async function createProduct(payload) {
    return window.App.api.post("/admin/products", payload);
  }

  async function updateProduct(productId, payload) {
    return window.App.api.request(`/admin/products/${productId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  async function updateWorkerAdmin(workerId, isAdmin) {
    return window.App.api.request(`/admin/workers/${workerId}/admin`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_admin: isAdmin })
    });
  }

  async function updateWorker(workerId, payload) {
  return window.App.api.request(`/admin/workers/${workerId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

  async function activateWorker(workerId) {
    return window.App.api.request(`/admin/workers/${workerId}/activate`, {
      method: "PATCH"
    });
  }

  async function deactivateWorker(workerId) {
    return window.App.api.request(`/admin/workers/${workerId}/deactivate`, {
      method: "PATCH"
    });
  }

  async function resetWorkerPassword(workerId, newPassword) {
    return window.App.api.request(`/admin/workers/${workerId}/reset-password`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_password: newPassword })
    });
  }

  async function listCategories() {
    return window.App.api.get("/admin/categories");
  }

  async function createCategory(name) {
    return window.App.api.post("/admin/categories", { name });
  }

  async function updateCategory(categoryId, payload) {
    return window.App.api.request(`/admin/categories/${categoryId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  async function listBrands() {
    return window.App.api.get("/admin/brands");
  }

  async function createBrand(name) {
    return window.App.api.post("/admin/brands", { name });
  }

  async function updateBrand(brandId, payload) {
    return window.App.api.request(`/admin/brands/${brandId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }



  async function openQrPdf(productIds, siteId) {
    const token = localStorage.getItem("lager_token");

    const response = await fetch(
      `/api/admin/products/qr-pdf?site_id=${siteId}&product_ids=${productIds.join(",")}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    if (!response.ok) {
      throw new Error("QR PDF konnte nicht erstellt werden.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    window.open(url, "_blank");
  }


  async function listStandorte() {
    return window.App.api.get("/admin/sites");
  }

  async function createStandort(name) {
    return window.App.api.post("/admin/sites", { name });
  }

  async function updateStandort(siteId, payload) {
    return window.App.api.request(`/admin/sites/${siteId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  async function listLocations(siteId = null) {
    const suffix = siteId ? `?site_id=${encodeURIComponent(siteId)}` : "";
    return window.App.api.get(`/admin/locations${suffix}`);
  }

  async function createLocation(payload) {
    return window.App.api.post("/admin/locations", payload);
  }

  async function updateLocation(locationId, payload) {
    return window.App.api.request(`/admin/locations/${locationId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  async function listProductStandortLocations() {
    return window.App.api.get("/admin/product-site-locations");
  }

  async function setDefaultProductLocation(productId, payload) {
    return window.App.api.request(`/admin/products/${productId}/default-location`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  window.App = window.App || {};
  window.App.adminApi = {
    listWorkers,
    createWorker,
    updateWorker,
    listProducts,
    createProduct,
    updateProduct,
    updateWorkerAdmin,
    activateWorker,
    deactivateWorker,
    updateWorker,
    resetWorkerPassword,
    listCategories,
    createCategory,
    updateCategory,
    listBrands,
    createBrand,
    updateBrand,
    listStandorte,
    createStandort,
    updateStandort,
    listLocations,
    createLocation,
    updateLocation,
    listProductStandortLocations,
    setDefaultProductLocation,
    openQrPdf
  };
})();
