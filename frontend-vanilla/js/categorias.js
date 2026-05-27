const API_BASE_URL = window.RUTABYTE_API_BASE_URL || document.body?.dataset.apiBaseUrl || "http://127.0.0.1:8000";
const CATEGORIAS_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/productos/categorias`;
const authToken = window.RutaByteAuthGuard?.requireAuth?.();

const alertSlot = document.getElementById("alertSlot");
const tableBody = document.getElementById("categoriasTableBody");
const categoriaModal = document.getElementById("categoriaModal");
const categoriaForm = document.getElementById("categoriaForm");
const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");

let categoriasCache = [];
let editingId = null;

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

function openModal(focusId) {
  categoriaModal.classList.add("is-open");
  categoriaModal.setAttribute("aria-hidden", "false");
  if (focusId) document.getElementById(focusId)?.focus();
}

function closeModal() {
  categoriaModal.classList.remove("is-open");
  categoriaModal.setAttribute("aria-hidden", "true");
  categoriaForm.reset();
  editingId = null;
  document.getElementById("modalTitle").textContent = "Crear Categoría";
  document.getElementById("modalEyebrow").textContent = "Nuevo registro";
}

async function apiRequest(url, options = {}) {
  if (!authToken) throw new Error("No se encontró un JWT.");
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${authToken}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(url, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = (payload && typeof payload === "object" && (payload.detail || payload.message || payload.error)) || `Error HTTP ${response.status}`;
    throw new Error(message);
  }
  return payload;
}

function renderCategorias() {
  if (!categoriasCache.length) {
    tableBody.innerHTML = '<tr><td colspan="4" class="empty-state">No hay categorías registradas.</td></tr>';
    return;
  }
  tableBody.innerHTML = categoriasCache.map((c) => {
    const activo = c.activa ?? true;
    const estadoClass = activo ? "tag tag--active" : "tag tag--inactive";
    const estadoText = activo ? "Activa" : "Inactiva";
    return `
      <tr>
        <td>${c.id}</td>
        <td><strong>${escapeHtml(c.nombre)}</strong></td>
        <td><span class="${estadoClass}">${estadoText}</span></td>
        <td>
          <button class="table-action" type="button" data-action="edit" data-id="${c.id}">Editar</button>
          <button class="table-action" type="button" data-action="toggle" data-id="${c.id}">${activo ? "Desactivar" : "Activar"}</button>
        </td>
      </tr>
    `;
  }).join("");
}

async function loadCategorias() {
  try {
    tableBody.innerHTML = '<tr><td colspan="4" class="empty-state">Cargando categorías...</td></tr>';
    const data = await apiRequest(CATEGORIAS_URL);
    categoriasCache = Array.isArray(data) ? data : [];
    renderCategorias();
  } catch (error) {
    tableBody.innerHTML = '<tr><td colspan="4" class="empty-state">Error cargando categorías.</td></tr>';
    showAlert(error.message);
  }
}

async function saveCategoria(event) {
  event.preventDefault();
  const nombre = categoriaForm.nombre.value.trim();
  if (!nombre) return;
  try {
    if (editingId) {
      await apiRequest(`${CATEGORIAS_URL}/${editingId}`, {
        method: "PUT",
        body: JSON.stringify({ nombre }),
      });
      showAlert("Categoría actualizada correctamente.", "success");
    } else {
      await apiRequest(CATEGORIAS_URL, {
        method: "POST",
        body: JSON.stringify({ nombre }),
      });
      showAlert("Categoría creada correctamente.", "success");
    }
    closeModal();
    await loadCategorias();
  } catch (error) {
    showAlert(error.message);
  }
}

async function deactivateCategoria(id) {
  const cat = categoriasCache.find((c) => String(c.id) === String(id));
  const activa = cat?.activa ?? true;
  if (!window.confirm(activa ? "¿Deseas desactivar esta categoría? Todos los productos asociados ocultarán su categoría." : "¿Deseas activar esta categoría?")) return;
  try {
    await apiRequest(`${CATEGORIAS_URL}/${id}`, { method: "DELETE" });
    showAlert(activa ? "Categoría desactivada correctamente." : "Categoría activada correctamente.", "success");
    await loadCategorias();
  } catch (error) {
    showAlert(error.message);
  }
}

tableBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const id = button.dataset.id;
  if (!id) return;

  if (button.dataset.action === "toggle") {
    void deactivateCategoria(id);
  } else if (button.dataset.action === "edit") {
    const cat = categoriasCache.find((c) => String(c.id) === String(id));
    if (!cat) return;
    editingId = id;
    document.getElementById("modalTitle").textContent = "Editar Categoría";
    document.getElementById("modalEyebrow").textContent = "Modificar registro";
    categoriaForm.nombre.value = cat.nombre;
    openModal("nombre");
  }
});

openModalBtn.addEventListener("click", () => {
  editingId = null;
  categoriaForm.reset();
  document.getElementById("modalTitle").textContent = "Crear Categoría";
  document.getElementById("modalEyebrow").textContent = "Nuevo registro";
  openModal("nombre");
});

closeModalBtn.addEventListener("click", closeModal);
cancelModalBtn.addEventListener("click", closeModal);
categoriaForm.addEventListener("submit", saveCategoria);

categoriaModal.addEventListener("click", (event) => {
  if (event.target === categoriaModal) closeModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && categoriaModal.classList.contains("is-open")) {
    closeModal();
  }
});

if (authToken) {
  void loadCategorias();
}
