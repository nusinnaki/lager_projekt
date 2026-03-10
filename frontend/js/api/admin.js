(function () {
  async function listUsers() {
    return window.App.api.get("/admin/users");
  }

  async function listCategories() {
    return window.App.api.get("/admin/categories");
  }

  async function createCategory(name) {
    return window.App.api.post("/admin/categories", { name });
  }

  async function listProducts() {
    return window.App.api.get("/admin/products");
  }

  async function updateProduct(productId, payload) {
    return window.App.api.request(`/admin/products/${productId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  async function updateUserAdmin(userId, isAdmin) {
    return window.App.api.request(`/admin/users/${userId}/admin`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_admin: isAdmin })
    });
  }

  async function resetUserPassword(userId, newPassword) {
    return window.App.api.request(`/admin/users/${userId}/reset-password`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_password: newPassword })
    });
  }

  window.App = window.App || {};
  window.App.adminApi = {
    listUsers,
    listCategories,
    createCategory,
    listProducts,
    updateProduct,
    updateUserAdmin,
    resetUserPassword
  };
})();
