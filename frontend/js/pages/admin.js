(function () {
  const token = localStorage.getItem("lager_token");
  const userRaw = localStorage.getItem("lager_user");

  const usersSection = document.getElementById("usersSection");
  const productsSection = document.getElementById("productsSection");
  const sitesSection = document.getElementById("sitesSection");
  const logsSection = document.getElementById("logsSection");

  const tabUsers = document.getElementById("tabUsers");
  const tabProducts = document.getElementById("tabProducts");
  const tabSites = document.getElementById("tabSites");
  const tabLogs = document.getElementById("tabLogs");
  const backToLagerBtn = document.getElementById("backToLagerBtn");

  const usersBody = document.getElementById("usersBody");
  const productsBody = document.getElementById("productsBody");
  const sitesBody = document.getElementById("sitesBody");
  const adminLogsBody = document.getElementById("adminLogsBody");

  const workerForm = document.getElementById("workerForm");
  const workerFirstName = document.getElementById("workerFirstName");
  const workerLastName = document.getElementById("workerLastName");
  const workerUsername = document.getElementById("workerUsername");
  const workerAdmin = document.getElementById("workerAdmin");
  const workerActive = document.getElementById("workerActive");
  const newWorkerBtn = document.getElementById("newWorkerBtn");
  const cancelWorkerCreateBtn = document.getElementById("cancelWorkerCreateBtn");

  const productForm = document.getElementById("productForm");
  const productSearch = document.getElementById("productSearch");
  const productName = document.getElementById("productName");
  const productNc = document.getElementById("productNc");
  const productNcLabel = document.getElementById("productNcLabel");
  const productCategory = document.getElementById("productCategory");
  const productCategoryNew = document.getElementById("productCategoryNew");
  const productCategoryNewLabel = document.getElementById("productCategoryNewLabel");
  const productBrand = document.getElementById("productBrand");
  const productBrandNew = document.getElementById("productBrandNew");
  const productBrandNewLabel = document.getElementById("productBrandNewLabel");
  const productActive = document.getElementById("productActive");
  const newProductBtn = document.getElementById("newProductBtn");
  const cancelProductBtn = document.getElementById("cancelProductBtn");
  const printQrBtn = document.getElementById("printQrBtn");
  const cancelQrModeBtn = document.getElementById("cancelQrModeBtn");
  const qrStandortModal = document.getElementById("qrStandortModal");
  const qrStandortSelect = document.getElementById("qrStandortSelect");
  const qrStandortConfirmBtn = document.getElementById("qrStandortConfirmBtn");
  const qrStandortCancelBtn = document.getElementById("qrStandortCancelBtn");
const siteForm = document.getElementById("siteForm");
  const siteName = document.getElementById("siteName");
  const siteActive = document.getElementById("siteActive");
  const newStandortBtn = document.getElementById("newStandortBtn");

  const adminMsg = document.getElementById("adminMsg");

  let allWorkers = [];
  let allProducts = [];
  let allCategories = [];
  let allBrands = [];
  let allStandorte = [];

  let editingWorkerId = null;
  let editingProductId = null;
  let editingStandortId = null;

  function esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

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
    usersSection?.classList.toggle("hidden", name !== "users");
    productsSection?.classList.toggle("hidden", name !== "products");
    sitesSection?.classList.toggle("hidden", name !== "sites");
    logsSection?.classList.toggle("hidden", name !== "logs");

    tabUsers?.classList.toggle("primary", name === "users");
    tabProducts?.classList.toggle("primary", name === "products");
    tabSites?.classList.toggle("primary", name === "sites");
    tabLogs?.classList.toggle("primary", name === "logs");

    if (name === "logs") {
      loadLogs().catch((err) => {
        console.error(err);
        setMsg("Logs konnten nicht geladen werden.", "error");
      });
    }
  }

  function usernameFromName(firstName, lastName) {
    const first = String(firstName || "").trim().toLowerCase().replaceAll(" ", "");
    const last = String(lastName || "").trim().toLowerCase().replaceAll(" ", "");
    if (!first || !last) return "";
    return `${first}.${last}`;
  }

  function clearWorkerFormForCreate() {
    editingWorkerId = null;
    workerForm?.classList.remove("hidden");
    newWorkerBtn?.classList.add("hidden");

    if (workerFirstName) workerFirstName.value = "";
    if (workerLastName) workerLastName.value = "";
    if (workerUsername) workerUsername.value = "";
    if (workerAdmin) workerAdmin.value = "false";
    if (workerActive) workerActive.value = "true";

    setMsg("Neuen Mitarbeiter anlegen.", "");
  }

  function renderWorkers(rows) {
    if (!usersBody) return;
    usersBody.innerHTML = "";

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const isEditing = Number(editingWorkerId) === Number(row.id);
      const roleLabel = row.is_admin ? "Admin" : "Techniker";

      if (isEditing) {
        const roleValue = row.is_admin ? "true" : "false";
        const activeValue = row.is_active ? "true" : "false";

        tr.innerHTML = `
          <td></td>
          <td>${row.id}</td>
          <td><input class="workerFirstNameCell" type="text" value="${esc(row.first_name)}" /></td>
          <td><input class="workerLastNameCell" type="text" value="${esc(row.last_name)}" /></td>
          <td><input class="workerUsernameCell" type="text" value="${esc(row.username)}" /></td>
          <td>
            <select class="workerAdminCell">
              <option value="false" ${roleValue === "false" ? "selected" : ""}>Techniker</option>
              <option value="true" ${roleValue === "true" ? "selected" : ""}>Admin</option>
            </select>
          </td>
          <td>
            <select class="workerActiveCell">
              <option value="true" ${activeValue === "true" ? "selected" : ""}>Ja</option>
              <option value="false" ${activeValue === "false" ? "selected" : ""}>Nein</option>
            </select>
          </td>
          <td>
            <div class="inline-worker-password-actions">
              <input class="workerPasswordCell" type="password" value="" placeholder="Neues Passwort" autocomplete="new-password" />
              <div class="inline-worker-actions">
                <button class="saveWorkerBtn" type="button">Speichern</button>
                <button class="cancelWorkerBtn" type="button">Abbrechen</button>
              </div>
            </div>
          </td>
        `;

        tr.querySelector(".saveWorkerBtn")?.addEventListener("click", async () => {
          try {
            await window.App.adminApi.updateWorker(row.id, {
              first_name: tr.querySelector(".workerFirstNameCell")?.value.trim() || "",
              last_name: tr.querySelector(".workerLastNameCell")?.value.trim() || "",
              username: tr.querySelector(".workerUsernameCell")?.value.trim().toLowerCase() || "",
              is_admin: tr.querySelector(".workerAdminCell")?.value === "true",
              is_active: tr.querySelector(".workerActiveCell")?.value === "true",
              auth_provider: "local",
              ldap_dn: null
            });

            const newPassword = tr.querySelector(".workerPasswordCell")?.value.trim() || "";
            if (newPassword) {
              await window.App.adminApi.resetWorkerPassword(row.id, newPassword);
            }

            editingWorkerId = null;
            setMsg("Mitarbeiter gespeichert.", "success");
            await loadWorkers();
          } catch (err) {
            console.error(err);
            setMsg(err.message || "Mitarbeiter konnte nicht gespeichert werden.", "error");
          }
        });

        tr.querySelector(".cancelWorkerBtn")?.addEventListener("click", () => {
          editingWorkerId = null;
          renderWorkers(allWorkers);
        });
      } else {
        tr.innerHTML = `
          <td>${row.id}</td>
          <td>${esc(row.first_name)}</td>
          <td>${esc(row.last_name)}</td>
          <td>${esc(row.username)}</td>
          <td>${roleLabel}</td>
          <td>${row.is_active ? "Ja" : "Nein"}</td>
          <td>
            <button class="editWorkerBtn" type="button">Bearbeiten</button>
          </td>
        `;

        tr.querySelector(".editWorkerBtn")?.addEventListener("click", () => {
          editingWorkerId = row.id;
          renderWorkers(allWorkers);
        });
      }

      usersBody.appendChild(tr);
    });
  }

  function selectedBrandName() {
    if ((productBrand?.value || "") === "__new__") return "";

    const selected = allBrands.find(
      (b) => Number(b.id) === Number(productBrand?.value || 0)
    );

    return String(selected?.name || "").trim();
  }

  function syncProductFormVisibility() {
    const categoryIsNew = (productCategory?.value || "") === "__new__";
    const brandIsNew = (productBrand?.value || "") === "__new__";
    const isNetcom = selectedBrandName().toLowerCase() === "netcom";

    productCategoryNewLabel?.classList.toggle("hidden", !categoryIsNew);
    productCategoryNew?.classList.toggle("hidden", !categoryIsNew);
    if (!categoryIsNew && productCategoryNew) productCategoryNew.value = "";

    productBrandNewLabel?.classList.toggle("hidden", !brandIsNew);
    productBrandNew?.classList.toggle("hidden", !brandIsNew);
    if (!brandIsNew && productBrandNew) productBrandNew.value = "";

    productNcLabel?.classList.toggle("hidden", !isNetcom);
    productNc?.classList.toggle("hidden", !isNetcom);
    if (!isNetcom && productNc) productNc.value = "";
  }

  function categoryOptions(selectedId) {
    return allCategories.map((c) =>
      `<option value="${c.id}" ${Number(c.id) === Number(selectedId) ? "selected" : ""}>${esc(c.name)}</option>`
    ).join("") + `<option value="__new__">Neue Kategorie</option>`;
  }

  function brandOptions(selectedId) {
    return allBrands.map((b) =>
      `<option value="${b.id}" ${Number(b.id) === Number(selectedId) ? "selected" : ""}>${esc(b.name)}</option>`
    ).join("") + `<option value="__new__">Neue Brand</option>`;
  }

  function fillProductFormForCreate() {
    editingProductId = null;
    productForm?.classList.remove("hidden");
    newProductBtn?.classList.add("hidden");

    if (productName) productName.value = "";
    if (productNc) productNc.value = "";
    if (productCategoryNew) productCategoryNew.value = "";
    if (productBrandNew) productBrandNew.value = "";
    if (productCategory) productCategory.innerHTML = categoryOptions(allCategories[0]?.id);
    if (productBrand) productBrand.innerHTML = brandOptions(allBrands[0]?.id);
    if (productActive) productActive.value = "true";

    syncProductFormVisibility();
    setMsg("Neues Produkt anlegen.", "");
  }

  function productRowsForDisplay() {
    const q = (productSearch?.value || "").trim().toLowerCase();
    if (!q) return allProducts;

    return allProducts.filter((row) =>
      String(row.id).includes(q) ||
      String(row.product_name || "").toLowerCase().includes(q) ||
      String(row.nc_nummer || "").toLowerCase().includes(q) ||
      String(row.category_name || "").toLowerCase().includes(q) ||
      String(row.brand_name || "").toLowerCase().includes(q)
    );
  }

  function renderProducts(rows) {
    if (!productsBody) return;
    productsBody.innerHTML = "";

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const isEditing = Number(editingProductId) === Number(row.id);
      const activeValue = row.active ? "true" : "false";

      if (isEditing) {
        tr.innerHTML = `
          <td>${row.id}</td>
          <td><input class="productNameCell" type="text" value="${esc(row.product_name)}" /></td>
          <td><select class="productCategoryCell">${categoryOptions(row.category_id)}</select></td>
          <td><select class="productBrandCell">${brandOptions(row.brand_id)}</select></td>
          <td><input class="productNcCell" type="text" value="${esc(row.nc_nummer)}" /></td>
          <td>
            <select class="productActiveCell">
              <option value="true" ${activeValue === "true" ? "selected" : ""}>Ja</option>
              <option value="false" ${activeValue === "false" ? "selected" : ""}>Nein</option>
            </select>
          </td>
          <td>
            <div class="product-edit-actions">
              <button class="saveProductRowBtn" type="button">Speichern</button>
              <button class="cancelProductRowBtn" type="button">Abbrechen</button>
            </div>

            <div class="product-location-editor">
              <div class="mini-title">Lagerplatz</div>

              <select class="productLocationStandortCell"></select>
              <select class="productLocationCell"></select>

              <button class="saveProductLocationBtn" type="button">
                Lagerplatz speichern
              </button>
            </div>
          </td>
        `;

        const productLocationStandortSelect = tr.querySelector(".productLocationStandortCell");
        const productLocationSelect = tr.querySelector(".productLocationCell");

        if (productLocationStandortSelect) {
          productLocationStandortSelect.innerHTML = allStandorte
            .map((site) => `
              <option value="${site.id}">
                ${site.name}
              </option>
            `)
            .join("");
        }

        async function loadProductLocationsForSelectedStandort() {
          const siteId = Number(productLocationStandortSelect?.value || 0);

          if (!siteId || !productLocationSelect) return;

          const locations = await window.App.adminApi.listLocations(siteId);

          productLocationSelect.innerHTML =
            `<option value="">Lagerplatz wählen</option>` +
            (locations || []).map((loc) => `
              <option value="${loc.id}">
                Regal ${loc.shelf} / Fach ${loc.row}
              </option>
            `).join("");
        }

        productLocationStandortSelect?.addEventListener("change", () => {
          loadProductLocationsForSelectedStandort().catch((err) => {
            console.error(err);
            setMsg("Lagerplätze konnten nicht geladen werden.", "error");
          });
        });

        loadProductLocationsForSelectedStandort().catch((err) => {
          console.error(err);
          setMsg("Lagerplätze konnten nicht geladen werden.", "error");
        });

        tr.querySelector(".saveProductLocationBtn")?.addEventListener("click", async () => {
          try {
            const siteId = Number(productLocationStandortSelect?.value || 0);
            const locationId = Number(productLocationSelect?.value || 0);

            if (!siteId || !locationId) {
              setMsg("Bitte Standort und Lagerplatz auswählen.", "error");
              return;
            }

            await window.App.adminApi.setDefaultProductLocation(row.id, {
              site_id: siteId,
              location_id: locationId
            });

            setMsg("Lagerplatz gespeichert.", "success");
          } catch (err) {
            console.error(err);
            setMsg(err.message || "Lagerplatz konnte nicht gespeichert werden.", "error");
          }
        });

        tr.querySelector(".saveProductRowBtn")?.addEventListener("click", async () => {
          try {
            await window.App.adminApi.updateProduct(row.id, {
              product_name: tr.querySelector(".productNameCell")?.value.trim() || "",
              category_id: Number(tr.querySelector(".productCategoryCell")?.value || 0),
              brand_id: Number(tr.querySelector(".productBrandCell")?.value || 0),
              nc_nummer: tr.querySelector(".productNcCell")?.value.trim() || null,
              active: tr.querySelector(".productActiveCell")?.value === "true"
            });

            editingProductId = null;
            setMsg("Produkt gespeichert.", "success");
            await loadProducts();
          } catch (err) {
            console.error(err);
            setMsg(err.message || "Produkt konnte nicht gespeichert werden.", "error");
          }
        });

        tr.querySelector(".cancelProductRowBtn")?.addEventListener("click", () => {
          editingProductId = null;
          renderProducts(productRowsForDisplay());
        });
      } else {
        tr.innerHTML = `
          <td>
            ${
              qrSelectionMode
                ? `
                  <input
                    class="qrSelect"
                    type="checkbox"
                    value="${row.id}"
                  />
                `
                : ""
            }
          </td>

          <td>${row.id}</td>
          <td>${esc(row.product_name)}</td>
          <td>${esc(row.category_name)}</td>
          <td>${esc(row.brand_name)}</td>
          <td>${esc(row.nc_nummer)}</td>
          <td>${row.active ? "Ja" : "Nein"}</td>
          <td><button class="editProductBtn" type="button">Bearbeiten</button></td>
        `;

        tr.querySelector(".editProductBtn")?.addEventListener("click", () => {
          editingProductId = row.id;
          renderProducts(productRowsForDisplay());
        });
      }

      const checkbox = tr.querySelector(".qrSelect");

      checkbox?.addEventListener("change", () => {
        updateQrButtonState();
      });

      productsBody.appendChild(tr);
    });
  }

  function fillStandortFormForCreate() {
    editingStandortId = null;
    siteForm?.classList.remove("hidden");

    if (siteName) siteName.value = "";
    if (siteActive) siteActive.value = "true";

    setMsg("Neuer Standort anlegen.", "");
  }

  function renderStandorte(rows) {
    if (!sitesBody) return;
    sitesBody.innerHTML = "";

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const isEditing = Number(editingStandortId) === Number(row.id);
      const activeValue = row.active ? "true" : "false";

      if (isEditing) {
        tr.innerHTML = `
          <td>${row.id}</td>
          <td><input class="siteNameCell" type="text" value="${esc(row.name)}" /></td>
          <td>
            <select class="siteActiveCell">
              <option value="true" ${activeValue === "true" ? "selected" : ""}>Ja</option>
              <option value="false" ${activeValue === "false" ? "selected" : ""}>Nein</option>
            </select>
          </td>
          <td>
            <button class="saveStandortRowBtn" type="button">Speichern</button>
            <button class="cancelStandortRowBtn" type="button">Abbrechen</button>
          </td>
        `;

        tr.querySelector(".saveStandortRowBtn")?.addEventListener("click", async () => {
          try {
            await window.App.adminApi.updateStandort(row.id, {
              name: tr.querySelector(".siteNameCell")?.value.trim() || "",
              active: tr.querySelector(".siteActiveCell")?.value === "true"
            });

            editingStandortId = null;
            setMsg("Standort gespeichert.", "success");
            await loadStandorte();
          } catch (err) {
            console.error(err);
            setMsg(err.message || "Standort konnte nicht gespeichert werden.", "error");
          }
        });

        tr.querySelector(".cancelStandortRowBtn")?.addEventListener("click", () => {
          editingStandortId = null;
          renderStandorte(allStandorte);
        });
      } else {
        tr.innerHTML = `
          <td>${row.id}</td>
          <td>${esc(row.name)}</td>
          <td>${row.active ? "Ja" : "Nein"}</td>
          <td><button class="editStandortBtn" type="button">Bearbeiten</button></td>
        `;

        tr.querySelector(".editStandortBtn")?.addEventListener("click", () => {
          editingStandortId = row.id;
          renderStandorte(allStandorte);
        });
      }

      sitesBody.appendChild(tr);
    });
  }

  function renderLogs(rows) {
    if (!adminLogsBody) return;
    adminLogsBody.innerHTML = "";

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const workerName = `${row.first_name || ""} ${row.last_name || ""}`.trim();
      const actionLabel =
        row.action === "load" ? "Einlagern" :
        row.action === "take" ? "Entnehmen" :
        row.action || "";

      tr.innerHTML = `
        <td>${row.id}</td>
        <td>${row.created_at || ""}</td>
        <td>${actionLabel}</td>
        <td>${row.product_id || ""}</td>
        <td>${esc(row.product_name)}</td>
        <td>${row.quantity || ""}</td>
        <td>${esc(row.site_name)}</td>
        <td>${row.shelf ?? ""}</td>
        <td>${row.row ?? ""}</td>
        <td>${esc(workerName)}</td>
      `;

      adminLogsBody.appendChild(tr);
    });
  }

  async function loadWorkers() {
    allWorkers = await window.App.adminApi.listWorkers() || [];
    renderWorkers(allWorkers);
  }

  async function loadReferenceData() {
    const [categories, brands] = await Promise.all([
      window.App.adminApi.listCategories(),
      window.App.adminApi.listBrands()
    ]);

    allCategories = categories || [];
    allBrands = brands || [];

    if (productCategory) productCategory.innerHTML = categoryOptions(allCategories[0]?.id);
    if (productBrand) productBrand.innerHTML = brandOptions(allBrands[0]?.id);
  }

  async function loadProducts() {
    allProducts = await window.App.adminApi.listProducts() || [];
    renderProducts(productRowsForDisplay());
  }

  async function loadStandorte() {
    allStandorte = await window.App.adminApi.listStandorte() || [];
    renderStandorte(allStandorte);
  }

  async function loadLogs() {
    const rows = await window.App.historyApi.listLogs(100, 0);
    renderLogs(rows || []);
  }

  tabUsers?.addEventListener("click", () => showTab("users"));
  tabProducts?.addEventListener("click", () => showTab("products"));
  tabSites?.addEventListener("click", () => showTab("sites"));
  tabLogs?.addEventListener("click", () => showTab("logs"));
  backToLagerBtn?.addEventListener("click", () => redirect("/lager"));

  newWorkerBtn?.addEventListener("click", clearWorkerFormForCreate);

  cancelWorkerCreateBtn?.addEventListener("click", () => {
    workerForm?.classList.add("hidden");
    newWorkerBtn?.classList.remove("hidden");
  });

  workerFirstName?.addEventListener("input", () => {
    if (!workerUsername) return;
    workerUsername.value = usernameFromName(workerFirstName.value, workerLastName?.value || "");
  });

  workerLastName?.addEventListener("input", () => {
    if (!workerUsername) return;
    workerUsername.value = usernameFromName(workerFirstName?.value || "", workerLastName.value);
  });

  workerForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const firstName = workerFirstName?.value.trim() || "";
    const lastName = workerLastName?.value.trim() || "";

    if (!firstName || !lastName) {
      setMsg("Vorname und Nachname sind erforderlich.", "error");
      return;
    }

    try {
      await window.App.adminApi.createWorker({
        first_name: firstName,
        last_name: lastName
      });

      workerForm?.classList.add("hidden");
      newWorkerBtn?.classList.remove("hidden");
      setMsg("Mitarbeiter gespeichert.", "success");
      await loadWorkers();
    } catch (err) {
      console.error(err);
      setMsg(err.message || "Mitarbeiter konnte nicht gespeichert werden.", "error");
    }
  });

  newProductBtn?.addEventListener("click", fillProductFormForCreate);

  cancelProductBtn?.addEventListener("click", () => {
    productForm?.classList.add("hidden");
    newProductBtn?.classList.remove("hidden");
  });

  productCategory?.addEventListener("change", syncProductFormVisibility);
  productBrand?.addEventListener("change", syncProductFormVisibility);


  


  let qrSelectionMode = false;

  function selectedQrProducts() {
    return Array.from(
      document.querySelectorAll(".qrSelect:checked")
    ).map((x) => Number(x.value));
  }

  function updateQrButtonState() {
    const selected = selectedQrProducts();

    if (!qrSelectionMode) {
      printQrBtn.textContent = "QR Codes";
      printQrBtn.disabled = false;

      cancelQrModeBtn?.classList.add("hidden");

      return;
    }

    printQrBtn.textContent =
      selected.length
        ? `Drucken (${selected.length})`
        : "Drucken";

    printQrBtn.disabled = selected.length === 0;
  }

  function exitQrMode() {
    qrSelectionMode = false;

    document
      .querySelectorAll(".qrSelect")
      .forEach((x) => {
        x.checked = false;
      });

    renderProducts(productRowsForDisplay());
    updateQrButtonState();
  }

  function openQrStandortModal() {
    if (!qrStandortSelect) return;

    qrStandortSelect.innerHTML = allStandorte
      .map((site) => `
        <option value="${site.id}">
          ${site.name}
        </option>
      `)
      .join("");

    qrStandortModal?.classList.remove("hidden");
  }

  printQrBtn?.addEventListener("click", async () => {
    try {
      if (!qrSelectionMode) {
        qrSelectionMode = true;

        cancelQrModeBtn?.classList.remove("hidden");

        renderProducts(productRowsForDisplay());

        printQrBtn.disabled = true;
        printQrBtn.textContent = "Drucken";

        return;
      }

      const selected = selectedQrProducts();

      if (!selected.length) {
        return;
      }

      openQrStandortModal();

    } catch (err) {
      console.error(err);
      setMsg(err.message || "QR PDF Fehler.", "error");
    }
  });

  cancelQrModeBtn?.addEventListener("click", () => {
    exitQrMode();
  });


  qrStandortCancelBtn?.addEventListener("click", () => {
    qrStandortModal?.classList.add("hidden");
  });

  qrStandortModal?.addEventListener("click", (event) => {
    if (event.target === qrStandortModal) {
      qrStandortModal.classList.add("hidden");
    }
  });

  qrStandortConfirmBtn?.addEventListener("click", async () => {
    try {
      const selected = selectedQrProducts();
      const siteId = Number(qrStandortSelect?.value || 0);

      if (!selected.length) {
        setMsg("Bitte Produkte auswählen.", "error");
        return;
      }

      if (!siteId) {
        setMsg("Bitte Standort auswählen.", "error");
        return;
      }

      await window.App.adminApi.openQrPdf(selected, siteId);

      qrStandortModal?.classList.add("hidden");
      exitQrMode();

    } catch (err) {
      console.error(err);
      setMsg(err.message || "QR PDF Fehler.", "error");
    }
  });

  productSearch?.addEventListener("input", () => {
    renderProducts(productRowsForDisplay());
  });

  productForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    try {
      let categoryId = Number(productCategory?.value || 0);
      let brandId = Number(productBrand?.value || 0);

      if ((productCategory?.value || "") === "__new__") {
        const newCategoryName = (productCategoryNew?.value || "").trim();
        if (!newCategoryName) throw new Error("Neue Kategorie fehlt.");

        await window.App.adminApi.createCategory(newCategoryName);
        await loadReferenceData();

        const createdCategory = allCategories.find(
          (c) => String(c.name || "").toLowerCase() === newCategoryName.toLowerCase()
        );

        if (!createdCategory) throw new Error("Neue Kategorie wurde nicht gefunden.");
        categoryId = Number(createdCategory.id);
      }

      if ((productBrand?.value || "") === "__new__") {
        const newBrandName = (productBrandNew?.value || "").trim();
        if (!newBrandName) throw new Error("Neue Brand fehlt.");

        await window.App.adminApi.createBrand(newBrandName);
        await loadReferenceData();

        const createdBrand = allBrands.find(
          (b) => String(b.name || "").toLowerCase() === newBrandName.toLowerCase()
        );

        if (!createdBrand) throw new Error("Neue Brand wurde nicht gefunden.");
        brandId = Number(createdBrand.id);
      }

      const brandName = String(
        allBrands.find((b) => Number(b.id) === Number(brandId))?.name || ""
      ).toLowerCase();

      await window.App.adminApi.createProduct({
        product_name: productName?.value.trim() || "",
        category_id: categoryId,
        brand_id: brandId,
        nc_nummer: brandName === "netcom" ? (productNc?.value.trim() || null) : null,
        active: productActive?.value === "true"
      });

      productForm?.classList.add("hidden");
      newProductBtn?.classList.remove("hidden");
      setMsg("Produkt angelegt.", "success");
      await loadReferenceData();
      await loadProducts();
    } catch (err) {
      console.error(err);
      setMsg(err.message || "Produkt konnte nicht angelegt werden.", "error");
    }
  });

  newStandortBtn?.addEventListener("click", fillStandortFormForCreate);

  siteForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    try {
      await window.App.adminApi.createStandort({
        name: siteName?.value.trim() || "",
        active: siteActive?.value === "true"
      });

      siteForm?.classList.add("hidden");
      setMsg("Standort angelegt.", "success");
      await loadStandorte();
    } catch (err) {
      console.error(err);
      setMsg(err.message || "Standort konnte nicht angelegt werden.", "error");
    }
  });

  showTab("users");

  async function initAdminPage() {
    try {
      await loadWorkers();
    } catch (err) {
      console.error("loadWorkers failed:", err);
      setMsg(err.message || "Mitarbeiter konnten nicht geladen werden.", "error");
    }

    try {
      await loadReferenceData();
    } catch (err) {
      console.error("loadReferenceData failed:", err);
      setMsg(err.message || "Referenzdaten konnten nicht geladen werden.", "error");
    }

    try {
      await loadProducts();
    } catch (err) {
      console.error("loadProducts failed:", err);
      setMsg(err.message || "Produkte konnten nicht geladen werden.", "error");
    }

    try {
      await loadStandorte();
    } catch (err) {
      console.error("loadStandorte failed:", err);
      setMsg(err.message || "Standorte konnten nicht geladen werden.", "error");
    }
  }

  initAdminPage();
})();
