(function () {
  const token = localStorage.getItem("lager_token");
  const userRaw = localStorage.getItem("lager_user");

  const usersSection = document.getElementById("usersSection");
  const categoriesSection = document.getElementById("categoriesSection");
  const productsSection = document.getElementById("productsSection");

  const tabUsers = document.getElementById("tabUsers");
  const tabCategories = document.getElementById("tabCategories");
  const tabProducts = document.getElementById("tabProducts");
  const backToLagerBtn = document.getElementById("backToLagerBtn");

  const usersBody = document.getElementById("usersBody");
  const categoriesBody = document.getElementById("categoriesBody");
  const newCategoryName = document.getElementById("newCategoryName");
  const createCategoryBtn = document.getElementById("createCategoryBtn");

  const productsList = document.getElementById("productsList");
  const productSearch = document.getElementById("productSearch");
  const productForm = document.getElementById("productForm");

  const productId = document.getElementById("productId");
  const productName = document.getElementById("productName");
  const productNc = document.getElementById("productNc");
  const productCategory = document.getElementById("productCategory");
  const thresholdRed = document.getElementById("thresholdRed");
  const thresholdYellow = document.getElementById("thresholdYellow");
  const lagerort = document.getElementById("lagerort");
  const regal = document.getElementById("regal");
  const fach = document.getElementById("fach");
  const productActive = document.getElementById("productActive");

  const adminMsg = document.getElementById("adminMsg");

  let allProducts = [];
  let allCategories = [];
  let allUsers = [];
  let selectedProductId = null;

  function setMsg(text, type = "") {
    if (!adminMsg) return;
    adminMsg.textContent = text || "";
    adminMsg.className = type ? `msg ${type}` : "msg";
  }

  function redirect(path) {
    window.location.href = path;
  }

  if (!token || !userRaw) {
    redirect("/");
    return;
  }

  try {
    const user = JSON.parse(userRaw);
    if (!user.is_admin) {
      redirect("/lager");
      return;
    }
  } catch {
    redirect("/");
    return;
  }

  function showTab(name) {
    usersSection.classList.toggle("hidden", name !== "users");
    categoriesSection.classList.toggle("hidden", name !== "categories");
    productsSection.classList.toggle("hidden", name !== "products");

    tabUsers.classList.toggle("primary", name === "users");
    tabCategories.classList.toggle("primary", name === "categories");
    tabProducts.classList.toggle("primary", name === "products");
  }

  async function handleToggleAdmin(user) {
    try {
      await window.App.adminApi.updateUserAdmin(user.id, !user.is_admin);
      setMsg("User-Rolle aktualisiert.", "success");
      await loadUsers();
    } catch (err) {
      setMsg(err.message || "Rolle konnte nicht geändert werden.", "error");
    }
  }

  async function handleResetPassword(user) {
    const newPassword = window.prompt(`Neues Passwort für ${user.username}:`);
    if (!newPassword) return;

    try {
      await window.App.adminApi.resetUserPassword(user.id, newPassword);
      setMsg("Passwort wurde zurückgesetzt.", "success");
    } catch (err) {
      setMsg(err.message || "Passwort konnte nicht zurückgesetzt werden.", "error");
    }
  }

  function renderUsers(rows) {
    usersBody.innerHTML = "";

    rows.forEach((row) => {
      const tr = document.createElement("tr");

      const roleLabel = row.is_admin ? "Admin" : "Techniker";
      const roleTarget = row.is_admin ? "Zu Techniker machen" : "Zu Admin machen";

      tr.innerHTML = `
        <td>${row.id}</td>
        <td>${row.username}</td>
        <td>${row.first_name} ${row.last_name}</td>
        <td>${roleLabel}</td>
        <td>${row.is_active ? "Ja" : "Nein"}</td>
        <td>
          <button class="toggleAdminBtn" type="button">${roleTarget}</button>
          <button class="resetPasswordBtn" type="button">Neues Passwort</button>
        </td>
      `;

      tr.querySelector(".toggleAdminBtn")?.addEventListener("click", () => handleToggleAdmin(row));
      tr.querySelector(".resetPasswordBtn")?.addEventListener("click", () => handleResetPassword(row));

      usersBody.appendChild(tr);
    });
  }

  function renderCategories(rows) {
    categoriesBody.innerHTML = "";
    productCategory.innerHTML = `<option value="">-</option>`;

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.id}</td>
        <td>${row.name}</td>
        <td>${row.active ? "Ja" : "Nein"}</td>
      `;
      categoriesBody.appendChild(tr);

      const opt = document.createElement("option");
      opt.value = row.id;
      opt.textContent = row.name;
      productCategory.appendChild(opt);
    });
  }

  function filterProducts() {
    const q = (productSearch.value || "").trim().toLowerCase();
    if (!q) return allProducts;

    return allProducts.filter((row) =>
      String(row.id).includes(q) ||
      String(row.product_name || "").toLowerCase().includes(q) ||
      String(row.nc_nummer || "").toLowerCase().includes(q)
    );
  }

  function fillProductForm(row) {
    productId.value = row.id ?? "";
    productName.value = row.product_name ?? "";
    productNc.value = row.nc_nummer ?? "";
    productCategory.value = row.category_id ?? "";
    thresholdRed.value = row.threshold_red ?? 5;
    thresholdYellow.value = row.threshold_yellow ?? 10;
    lagerort.value = row.lagerort ?? "";
    regal.value = row.regal ?? "";
    fach.value = row.fach ?? "";
    productActive.value = row.active ? "true" : "false";
  }

  function renderProductsList(rows) {
    productsList.innerHTML = "";

    rows.forEach((row) => {
      const div = document.createElement("div");
      div.className = "admin-item" + (row.id === selectedProductId ? " active" : "");
      div.textContent = `${row.id}  ${row.product_name}`;
      div.addEventListener("click", () => {
        selectedProductId = row.id;
        fillProductForm(row);
        renderProductsList(filterProducts());
      });
      productsList.appendChild(div);
    });
  }

  async function loadUsers() {
    const rows = await window.App.adminApi.listUsers();
    allUsers = rows || [];
    renderUsers(allUsers);
  }

  async function loadCategories() {
    const rows = await window.App.adminApi.listCategories();
    allCategories = rows || [];
    renderCategories(allCategories);
  }

  async function loadProducts() {
    const rows = await window.App.adminApi.listProducts();
    allProducts = rows || [];
    renderProductsList(filterProducts());

    if (!selectedProductId && allProducts.length) {
      selectedProductId = allProducts[0].id;
      fillProductForm(allProducts[0]);
      renderProductsList(filterProducts());
    }
  }

  tabUsers?.addEventListener("click", () => showTab("users"));
  tabCategories?.addEventListener("click", () => showTab("categories"));
  tabProducts?.addEventListener("click", () => showTab("products"));
  backToLagerBtn?.addEventListener("click", () => redirect("/lager"));

  createCategoryBtn?.addEventListener("click", async () => {
    const name = (newCategoryName.value || "").trim();
    if (!name) {
      setMsg("Kategoriename fehlt.", "error");
      return;
    }

    try {
      await window.App.adminApi.createCategory(name);
      newCategoryName.value = "";
      setMsg("Kategorie angelegt.", "success");
      await loadCategories();
    } catch (err) {
      setMsg(err.message || "Kategorie konnte nicht angelegt werden.", "error");
    }
  });

  productSearch?.addEventListener("input", () => {
    renderProductsList(filterProducts());
  });

  productForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const id = Number(productId.value || 0);
    if (!id) {
      setMsg("Kein Produkt ausgewählt.", "error");
      return;
    }

    const payload = {
      category_id: productCategory.value ? Number(productCategory.value) : null,
      threshold_red: Number(thresholdRed.value || 0),
      threshold_yellow: Number(thresholdYellow.value || 0),
      lagerort: lagerort.value || null,
      regal: regal.value || null,
      fach: fach.value || null,
      product_name: productName.value || "",
      nc_nummer: productNc.value || null,
      active: productActive.value === "true"
    };

    try {
      await window.App.adminApi.updateProduct(id, payload);
      setMsg("Produkt gespeichert.", "success");
      await loadProducts();
    } catch (err) {
      setMsg(err.message || "Produkt konnte nicht gespeichert werden.", "error");
    }
  });

  showTab("users");

  Promise.all([loadUsers(), loadCategories(), loadProducts()]).catch((err) => {
    setMsg(err.message || "Admin-Daten konnten nicht geladen werden.", "error");
  });
})();
