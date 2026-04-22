const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";
const PRODUCTOS_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/productos`;
const CATEGORIAS_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/productos/categorias`;

const alertSlot = document.getElementById("alertSlot");
const tableBody = document.getElementById("productosTableBody");

const productoModal = document.getElementById("productoModal");
const productoForm = document.getElementById("productoForm");
const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");
const categoriaSelect = document.getElementById("categoria_id");

const categoriaModal = document.getElementById("categoriaModal");
const categoriaForm = document.getElementById("categoriaForm");
const openCatModalBtn = document.getElementById("openCatModalBtn");
const closeCatModalBtn = document.getElementById("closeCatModalBtn");
const cancelCatModalBtn = document.getElementById("cancelCatModalBtn");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

let categoriasCache = [];
let currentProductos = [];
let editingId = null;

function getToken() {
  return authToken;
}

function showAlert(message, type = "error") {
  const alert = document.createElement("div");
  alert.className = `alert alert--${type}`;
  alert.setAttribute("role", "alert");
  alert.textContent = message;

  alertSlot.replaceChildren(alert);

  window.clearTimeout(showAlert.timeoutId);
  showAlert.timeoutId = window.setTimeout(() => {
    if (alertSlot.contains(alert)) alert.remove();
  }, 5000);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function openModal(modal, focusId) {
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  if (focusId) document.getElementById(focusId)?.focus();
}

function closeModal(modal) {
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  const form = modal.querySelector("form");
  if (form) form.reset();

  if (modal === productoModal) {
    editingId = null;
    document.getElementById("modalTitle").textContent = "Crear Producto";
  }
}

async function parseResponse(response) {
  const ct = response.headers.get("content-type") || "";
  return ct.includes("application/json") ? response.json() : response.text();
}

async function apiRequest(url, options = {}) {
  const token = getToken();
  if (!token) throw new Error("No se encontro un JWT en el almacenamiento del navegador.");

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...options, headers });
  const payload = await parseResponse(response);

  if (!response.ok) {
    const message =
      (payload && typeof payload === "object" && (payload.detail || payload.message || payload.error)) ||
      (typeof payload === "string" && payload.trim()) ||
      `La API respondio con error HTTP ${response.status}.`;
    throw new Error(message);
  }

  return payload;
}

function getList(payload) {
  if (Array.isArray(payload)) return payload;
  const containers = [payload?.data, payload?.items, payload?.result];
  for (const c of containers) {
    if (Array.isArray(c)) return c;
  }
  return [];
}

// ── Categorías ─────────────────────────────────────────────

async function loadCategorias() {
  try {
    const payload = await apiRequest(CATEGORIAS_URL);
    categoriasCache = getList(payload);
    categoriaSelect.innerHTML = '<option value="">Seleccionar categoria</option>';
    categoriasCache.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.nombre;
      categoriaSelect.appendChild(opt);
    });
  } catch {
    categoriasCache = [];
  }
}

function getCategoriaNombre(catId) {
  if (!catId) return "-";
  const cat = categoriasCache.find((c) => c.id === catId);
  return cat ? cat.nombre : String(catId);
}

async function createCategoria(event) {
  event.preventDefault();
  if (!authToken) return;

  const nombre = categoriaForm.catNombre.value.trim();

  try {
    await apiRequest(CATEGORIAS_URL, {
      method: "POST",
      body: JSON.stringify({ nombre }),
    });
    showAlert("Categoria creada correctamente.", "success");
    closeModal(categoriaModal);
    await loadCategorias();
  } catch (error) {
    showAlert(error.message);
  }
}

// ── Productos ──────────────────────────────────────────────

function formatPrice(value) {
  return Number(value).toLocaleString("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 });
}

function renderEmptyState() {
  tableBody.innerHTML = `
    <tr><td class="empty-state" colspan="6">No hay productos registrados todavia.</td></tr>
  `;
}

function renderProductos(productos) {
  if (!productos.length) {
    renderEmptyState();
    return;
  }

  const rows = productos.map((p) => {
    const id = p.id ?? p.producto_id;
    if (id == null) return "";

    const nombre = escapeHtml(p.nombre);
    const categoria = escapeHtml(getCategoriaNombre(p.categoria_id));
    const precio = formatPrice(p.precio);
    const desc = escapeHtml(p.descripcion || "-");
    const activo = p.activo ?? true;
    const estadoClass = activo ? "tag tag--active" : "tag tag--inactive";
    const estadoText = activo ? "Activo" : "Inactivo";
    const disabledAttr = activo ? "" : "disabled";

    return `
      <tr>
        <td>${nombre}</td>
        <td><span class="tag tag--role">${categoria}</span></td>
        <td>${precio}</td>
        <td class="desc-cell">${desc}</td>
        <td><span class="${estadoClass}">${estadoText}</span></td>
        <td>
          <button class="table-action" type="button" data-action="edit" data-id="${escapeHtml(id)}">
            Editar
          </button>
          <button class="table-action" type="button" data-action="deactivate" data-id="${escapeHtml(id)}" ${disabledAttr}>
            Desactivar
          </button>
        </td>
      </tr>
    `;
  });

  tableBody.innerHTML = "";
  tableBody.insertAdjacentHTML("beforeend", rows.filter(Boolean).join(""));
}

async function loadProductos() {
  if (!authToken) return;

  try {
    tableBody.innerHTML = `<tr><td class="empty-state" colspan="6">Cargando productos...</td></tr>`;
    const payload = await apiRequest(PRODUCTOS_URL);
    const lista = getList(payload);
    currentProductos = lista;
    renderProductos(lista);
  } catch (error) {
    renderEmptyState();
    showAlert(error.message);
  }
}

async function createProducto(event) {
  event.preventDefault();
  if (!authToken) return;

  const nombre = productoForm.nombre.value.trim();
  const categoria_id = Number(productoForm.categoria_id.value);
  const precio = Number(productoForm.precio.value);
  const descripcion = productoForm.descripcion.value.trim() || null;
  const url_imagen = productoForm.url_imagen.value.trim() || null;

  const payload = { nombre, categoria_id, precio, descripcion, url_imagen };

  try {
    if (editingId) {
      await apiRequest(`${PRODUCTOS_URL}/${editingId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showAlert("Producto actualizado correctamente.", "success");
    } else {
      await apiRequest(PRODUCTOS_URL, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("Producto creado correctamente.", "success");
    }

    editingId = null;
    closeModal(productoModal);
    await loadProductos();
  } catch (error) {
    showAlert(error.message);
  }
}

async function deactivateProducto(productoId) {
  if (!authToken) return;
  if (!window.confirm("Deseas desactivar este producto?")) return;

  try {
    await apiRequest(`${PRODUCTOS_URL}/${productoId}`, { method: "DELETE" });
    showAlert("Producto desactivado correctamente.", "success");
    await loadProductos();
  } catch (error) {
    showAlert(error.message);
  }
}

// ── Eventos ────────────────────────────────────────────────

tableBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  const id = button.dataset.id;
  if (!id) return;

  if (button.dataset.action === "deactivate") {
    void deactivateProducto(id);
    return;
  }

  if (button.dataset.action === "edit") {
    await loadCategorias();

    const producto = currentProductos.find((p) => String(p.id ?? p.producto_id) === String(id));
    if (!producto) {
      showAlert("No se pudo cargar el producto para editar.");
      return;
    }

    editingId = id;

    document.getElementById("modalTitle").textContent = "Editar Producto";
    productoForm.nombre.value = producto.nombre || "";
    productoForm.categoria_id.value = producto.categoria_id || "";
    productoForm.precio.value = producto.precio ?? "";
    productoForm.descripcion.value = producto.descripcion || "";
    productoForm.url_imagen.value = producto.url_imagen || "";

    openModal(productoModal, "nombre");
  }
});

openModalBtn.addEventListener("click", async () => {
  editingId = null;
  productoForm.reset();
  document.getElementById("modalTitle").textContent = "Crear Producto";
  await loadCategorias();
  openModal(productoModal, "nombre");
});
closeModalBtn.addEventListener("click", () => closeModal(productoModal));
cancelModalBtn.addEventListener("click", () => closeModal(productoModal));
productoForm.addEventListener("submit", createProducto);

openCatModalBtn.addEventListener("click", () => openModal(categoriaModal, "catNombre"));
closeCatModalBtn.addEventListener("click", () => closeModal(categoriaModal));
cancelCatModalBtn.addEventListener("click", () => closeModal(categoriaModal));
categoriaForm.addEventListener("submit", createCategoria);

if (authToken) {
  void loadCategorias().then(() => loadProductos());
}
