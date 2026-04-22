const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";

const MESAS_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/mesas`;
const SEDES_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/sedes`;  

const alertSlot = document.getElementById("alertSlot");
const tableBody = document.getElementById("mesasTableBody");

const mesaModal = document.getElementById("mesaModal");
const mesaForm = document.getElementById("mesaForm");
const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");
const sedeSelect = document.getElementById("sede_id");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

let currentMesas = [];
let sedesCache = [];
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

  if (modal === mesaModal) {
    editingId = null;
    document.getElementById("modalTitle").textContent = "Crear Mesa";
  }
}

async function parseResponse(response) {
  const ct = response.headers.get("content-type") || "";
  return ct.includes("application/json") ? response.json() : response.text();
}

async function apiRequest(url, options = {}) {
  const token = getToken();
  if (!token) throw new Error("No se encontro un JWT en el navegador.");

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

async function loadSedes() {
  try {
    const payload = await apiRequest(SEDES_URL);
    sedesCache = getList(payload);

    sedeSelect.innerHTML = '<option value="">Seleccionar sede</option>';
    sedesCache.forEach((sede) => {
      const opt = document.createElement("option");
      opt.value = sede.id;
      opt.textContent = sede.nombre;
      sedeSelect.appendChild(opt);
    });
  } catch (error) {
    sedesCache = [];
    showAlert(error.message);
  }
}

function getSedeNombre(sedeId) {
  const sede = sedesCache.find((s) => s.id === sedeId);
  return sede ? sede.nombre : `Sede ${sedeId ?? "-"}`;
}


function renderEmptyState() {
  tableBody.innerHTML = `
    <tr><td class="empty-state" colspan="4">No hay mesas registradas todavia.</td></tr>
  `;
}

function renderMesas(mesas) {
  if (!mesas.length) {
    renderEmptyState();
    return `
        <tr>
            <td>${escapeHtml(getSedeNombre(m.sede_id))}</td>
            <td>${identificador}</td>
            <td><span class="tag tag--role">${estado}</span></td>
            <td><span class="${estadoClass}">${estadoActivo}</span></td>
            <td>
            <button class="table-action" type="button" data-action="edit" data-id="${id}">
                Editar
            </button>
            <button class="table-action" type="button" data-action="deactivate" data-id="${id}" ${disabledAttr}>
                Desactivar
            </button>
            </td>
        </tr>
        `;
  }

  const rows = mesas.map((m) => {
    const id = m.id;
    const identificador = escapeHtml(m.identificador_mesa || m.numero || m.nombre || `Mesa ${id}`);
    const estado = escapeHtml(m.estado || "LIBRE");
    const activo = m.activa ?? m.activo ?? true;
    const estadoActivo = activo ? "Activa" : "Inactiva";
    const estadoClass = activo ? "tag tag--active" : "tag tag--inactive";
    const disabledAttr = activo ? "" : "disabled";

    return `
      <tr>
        <td>${identificador}</td>
        <td><span class="tag tag--role">${estado}</span></td>
        <td><span class="${estadoClass}">${estadoActivo}</span></td>
        <td>
          <button class="table-action" type="button" data-action="edit" data-id="${id}">
            Editar
          </button>
          <button class="table-action" type="button" data-action="deactivate" data-id="${id}" ${disabledAttr}>
            Desactivar
          </button>
        </td>
      </tr>
    `;
  });

  tableBody.innerHTML = "";
  tableBody.insertAdjacentHTML("beforeend", rows.join(""));
}

async function loadMesas() {
  if (!authToken) return;

  try {
    tableBody.innerHTML = `<tr><td class="empty-state" colspan="4">Cargando mesas...</td></tr>`;
    const payload = await apiRequest(MESAS_URL);
    const lista = getList(payload);
    currentMesas = lista;
    renderMesas(lista);
  } catch (error) {
    renderEmptyState();
    showAlert(error.message);
  }
}

async function saveMesa(event) {
  event.preventDefault();
  if (!authToken) return;

  const sede_id = Number(document.getElementById("sede_id").value);
  const identificador_mesa = mesaForm.identificador_mesa.value.trim();
  const estado = mesaForm.estado.value;

  const payload = { sede_id, identificador_mesa, estado };

  try {
    if (editingId) {
      await apiRequest(`${MESAS_URL}/${editingId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showAlert("Mesa actualizada correctamente.", "success");
    } else {
      await apiRequest(MESAS_URL, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("Mesa creada correctamente.", "success");
    }

    editingId = null;
    closeModal(mesaModal);
    await loadMesas();
  } catch (error) {
    showAlert(error.message);
  }
}

async function deactivateMesa(mesaId) {
  if (!authToken) return;
  if (!window.confirm("Deseas desactivar esta mesa?")) return;

  try {
    await apiRequest(`${MESAS_URL}/${mesaId}`, { method: "DELETE" });
    showAlert("Mesa desactivada correctamente.", "success");
    await loadMesas();
  } catch (error) {
    showAlert(error.message);
  }
}

tableBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  const id = button.dataset.id;
  if (!id) return;

  if (button.dataset.action === "deactivate") {
    void deactivateMesa(id);
    return;
  }

  if (button.dataset.action === "edit") {
    const mesa = currentMesas.find((m) => String(m.id) === String(id));
    if (!mesa) {
      showAlert("No se pudo cargar la mesa.");
      return;
    }

    editingId = id;

    document.getElementById("modalTitle").textContent = "Editar Mesa";
    document.getElementById("sede_id").value = mesa.sede_id || "";
    mesaForm.identificador_mesa.value = mesa.identificador_mesa || mesa.numero || mesa.nombre || "";
    mesaForm.estado.value = mesa.estado || "LIBRE";

    openModal(mesaModal, "identificador_mesa");
  }
});

openModalBtn.addEventListener("click", async () => {
  editingId = null;
  mesaForm.reset();
  document.getElementById("modalTitle").textContent = "Crear Mesa";
  mesaForm.estado.value = "LIBRE";
  await loadSedes();
  openModal(mesaModal, "sede_id");
});

closeModalBtn.addEventListener("click", () => closeModal(mesaModal));
cancelModalBtn.addEventListener("click", () => closeModal(mesaModal));
mesaForm.addEventListener("submit", saveMesa);

if (authToken) {
  void loadSedes().then(() => loadMesas());
}