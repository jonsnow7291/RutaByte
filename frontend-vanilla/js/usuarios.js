const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";
const USUARIOS_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/usuarios`;
const SEDES_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/sedes`;

const alertSlot = document.getElementById("alertSlot");
const tableBody = document.getElementById("usuariosTableBody");
const modal = document.getElementById("usuarioModal");
const form = document.getElementById("usuarioForm");
const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");
const sedeSelect = document.getElementById("sede_id");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

const ROLE_NAMES = { 1: "ADMIN", 2: "CAJERO", 3: "MESERO" };

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
    if (alertSlot.contains(alert)) {
      alert.remove();
    }
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

let editingId = null;

function openModal(editing = false) {
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  if (!editing) {
    editingId = null;
    form.reset();
  }
  document.getElementById("nombre").focus();
}

function closeModal() {
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  form.reset();
  editingId = null;
  form.correo.readOnly = false;
  form.correo.parentElement.style.display = "";
  form.contrasena.required = true;
  form.contrasena.placeholder = "Minimo 6 caracteres";

  const modalTitle = document.getElementById("modalTitle");
  const modalEyebrow = modal.parentElement.querySelector(".eyebrow");
  modalTitle.textContent = "Crear Usuario";
  modalEyebrow.textContent = "Nuevo registro";
  openModalBtn.focus();
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

async function apiRequest(url, options = {}) {
  const token = getToken();

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...options, headers });
  const payload = await response.json();

  if (!response.ok) {
    console.error("ERROR BACKEND:", payload); // 🔥 CLAVE

    let message = "Error en la solicitud";

    if (Array.isArray(payload.detail)) {
      message = payload.detail.map(e => e.msg).join(", ");
    } else if (payload.detail) {
      message = payload.detail;
    }

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

let sedesCache = [];

async function loadSedes() {
  try {
    const payload = await apiRequest(SEDES_URL);
    sedesCache = getList(payload);
    sedeSelect.innerHTML = '<option value="">Sin sede</option>';
    sedesCache.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.nombre;
      sedeSelect.appendChild(opt);
    });
  } catch {
    sedesCache = [];
  }
}

function getSedeNombre(sedeId) {
  if (!sedeId) return "-";
  const sede = sedesCache.find((s) => s.id === sedeId);
  return sede ? sede.nombre : String(sedeId);
}

function renderEmptyState() {
  tableBody.innerHTML = `
    <tr>
      <td class="empty-state" colspan="6">
        No hay usuarios registrados todavia.
      </td>
    </tr>
  `;
}

function renderUsuarios(usuarios) {
  if (!usuarios.length) {
    renderEmptyState();
    return;
  }

  const rows = usuarios.map((u) => {
    const id = u.id ?? u.usuario_id;
    if (id == null) return "";

    const nombre = escapeHtml(u.nombre);
    const correo = escapeHtml(u.correo);
    const rol = escapeHtml(ROLE_NAMES[u.rol_id] || `Rol ${u.rol_id}`);
    const sede = escapeHtml(getSedeNombre(u.sede_id));
    const activo = u.activo ?? true;
    const estadoClass = activo ? "tag tag--active" : "tag tag--inactive";
    const estadoText = activo ? "Activo" : "Inactivo";
    const disabledAttr = activo ? "" : "disabled";

    return `
      <tr>
        <td>${nombre}</td>
        <td>${correo}</td>
        <td><span class="tag tag--role">${rol}</span></td>
        <td>${sede}</td>
        <td><span class="${estadoClass}">${estadoText}</span></td>
        <td>
          <button
            class="table-action"
            type="button"
            data-action="edit"
            data-id="${escapeHtml(id)}"
          >
            Editar
          </button>
          <button
            class="table-action"
            type="button"
            data-action="deactivate"
            data-id="${escapeHtml(id)}"
            ${disabledAttr}
          >
            Desactivar
          </button>
        </td>
      </tr>
    `;
  });

  tableBody.innerHTML = "";
  tableBody.insertAdjacentHTML("beforeend", rows.filter(Boolean).join(""));
}

async function loadUsuarios() {
  if (!authToken) return;

  try {
    tableBody.innerHTML = `
      <tr>
        <td class="empty-state" colspan="6">Cargando usuarios...</td>
      </tr>
    `;
    const payload = await apiRequest(USUARIOS_URL);
    renderUsuarios(getList(payload));
  } catch (error) {
    renderEmptyState();
    showAlert(error.message);
  }
}

async function createUsuario(event) {
  event.preventDefault();

  const nombre = form.nombre.value.trim();
  const contrasena = form.contrasena.value;
  const rol_id = Number(form.rol_id.value);
  const sede_id = form.sede_id.value ? Number(form.sede_id.value) : null;

  try {
    if (editingId) {
      await apiRequest(`${USUARIOS_URL}/${editingId}`, {
        method: "PUT",
        body: JSON.stringify({
          nombre,
          contrasena: contrasena || null,
          rol_id,
          sede_id
        }),
      });
      showAlert("Usuario actualizado correctamente.", "success");
    } else {
      const correo = form.correo.value.trim();
      await apiRequest(USUARIOS_URL, {
        method: "POST",
        body: JSON.stringify({
          nombre,
          correo,
          contrasena: contrasena,
          rol_id,
          sede_id
        }),
      });
      showAlert("Usuario creado correctamente.", "success");
    }
    closeModal();
    await loadUsuarios();

  } catch (error) {
    console.error(error);
    showAlert(error.message);
  }
}

async function deactivateUsuario(usuarioId) {
  if (!authToken) return;
  if (!window.confirm("Deseas desactivar este usuario?")) return;

  try {
    await apiRequest(`${USUARIOS_URL}/${usuarioId}`, { method: "DELETE" });
    showAlert("Usuario desactivado correctamente.", "success");
    await loadUsuarios();
  } catch (error) {
    showAlert(error.message);
  }
}

async function editUsuario(usuarioId) {
  await loadSedes();
  const usuarios = await apiRequest(USUARIOS_URL);
  const usuario = getList(usuarios).find((u) => u.id === usuarioId);
  if (!usuario) {
    showAlert("Usuario no encontrado");
    return;
  }
  editingId = usuarioId;
  form.nombre.value = usuario.nombre;
  form.correo.value = usuario.correo;
  form.correo.readOnly = true;
  form.correo.parentElement.style.display = "none";
  form.contrasena.placeholder = "Nueva contrasena (opcional)";
  form.contrasena.required = false;
  form.rol_id.value = usuario.rol_id || "";
  form.sede_id.value = usuario.sede_id || "";

  const modalTitle = document.getElementById("modalTitle");
  const modalEyebrow = modal.parentElement.querySelector(".eyebrow");
  modalTitle.textContent = "Editar Usuario";
  modalEyebrow.textContent = "Editar registro";
  openModal(true);
}

tableBody.addEventListener("click", (event) => {
  const button = event.target.closest('[data-action="deactivate"]');
  if (button) {
    const id = button.dataset.id;
    if (id) void deactivateUsuario(id);
    return;
  }
  const editBtn = event.target.closest('[data-action="edit"]');
  if (editBtn) {
    const id = editBtn.dataset.id;
    if (id) void editUsuario(Number(id));
  }
});

openModalBtn.addEventListener("click", async () => {
  await loadSedes();
  openModal();
});
closeModalBtn.addEventListener("click", closeModal);
cancelModalBtn.addEventListener("click", closeModal);
form.addEventListener("submit", createUsuario);

if (authToken) {
  void loadSedes().then(() => loadUsuarios());
}
