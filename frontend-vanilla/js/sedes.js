const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";
const API_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/sedes`;

const alertSlot = document.getElementById("alertSlot");
const tableBody = document.getElementById("sedesTableBody");
const modal = document.getElementById("sedeModal");
const form = document.getElementById("sedeForm");
const modalTitle = document.getElementById("modalTitle");
const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

let currentEditingSedeId = null;

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

function openModal(editingId = null, initialData = {}) {
  currentEditingSedeId = editingId;
  if (editingId) {
    if (modalTitle) modalTitle.textContent = "Editar Sede";
    form.nombre.value = initialData.nombre || "";
    form.direccion.value = initialData.direccion || "";
    form.ciudad.value = initialData.ciudad || "";
  } else {
    if (modalTitle) modalTitle.textContent = "Crear Sede";
    form.reset();
  }
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  document.getElementById("nombre").focus();
}

function closeModal() {
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  form.reset();
  currentEditingSedeId = null;
  openModalBtn.focus();
}

function getSedesList(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  const containers = [payload?.data, payload?.items, payload?.sedes, payload?.result];
  for (const container of containers) {
    if (Array.isArray(container)) {
      return container;
    }
  }

  return [];
}

function renderEmptyState() {
  tableBody.innerHTML = `
    <tr>
      <td class="empty-state" colspan="5">
        No hay sedes registradas todavia.
      </td>
    </tr>
  `;
}

function renderSedes(sedes) {
  if (!sedes.length) {
    renderEmptyState();
    return;
  }

  const rows = sedes.map((sede) => {
    const sedeId = sede.id ?? sede.sede_id ?? sede.ID;
    if (sedeId == null || sedeId === "") {
      return "";
    }

    const nombre = escapeHtml(sede.nombre ?? sede.name ?? "-");
    const direccion = escapeHtml(sede.direccion ?? sede.address ?? "-");
    const ciudad = escapeHtml(sede.ciudad ?? sede.city ?? "-");
    const activa = sede.activa ?? sede.activa ?? true;
    const estadoClass = activa ? "tag tag--active" : "tag tag--inactive";
    const estadoText = activa ? "Activa" : "Inactiva";
    const disabledAttr = activa ? "" : "disabled";

    return `
      <tr>
        <td>${nombre}</td>
        <td>${direccion}</td>
        <td>${ciudad}</td>
        <td><span class="${estadoClass}">${estadoText}</span></td>
        <td>
          <div style="display: flex; gap: 8px;">
            <button
              class="table-action table-action--success"
              type="button"
              data-action="edit"
              data-id="${escapeHtml(sedeId)}"
              data-nombre="${nombre}"
              data-direccion="${direccion}"
              data-ciudad="${ciudad}"
            >
              Editar
            </button>
            <button
              class="table-action"
              type="button"
              data-action="deactivate"
              data-id="${escapeHtml(sedeId)}"
              ${disabledAttr}
            >
              Desactivar
            </button>
          </div>
        </td>
      </tr>
    `;
  });

  tableBody.innerHTML = "";
  tableBody.insertAdjacentHTML("beforeend", rows.filter(Boolean).join(""));
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
  if (!token) {
    throw new Error("No se encontro un JWT en el almacenamiento del navegador.");
  }

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

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

async function loadSedes() {
  if (!authToken) {
    return;
  }

  try {
    tableBody.innerHTML = `
      <tr>
        <td class="empty-state" colspan="5">Cargando sedes...</td>
      </tr>
    `;

    const payload = await apiRequest(API_URL);
    renderSedes(getSedesList(payload));
  } catch (error) {
    renderEmptyState();
    showAlert(error.message);
  }
}

async function submitSede(event) {
  event.preventDefault();

  if (!authToken) {
    return;
  }

  const nombre = form.nombre.value.trim();
  const direccion = form.direccion.value.trim();
  const ciudad = form.ciudad.value.trim();

  try {
    if (currentEditingSedeId) {
      // Edit mode (PUT)
      await apiRequest(`${API_URL}/${currentEditingSedeId}`, {
        method: "PUT",
        body: JSON.stringify({ nombre, direccion, ciudad }),
      });
      showAlert("Sede actualizada correctamente.", "success");
    } else {
      // Create mode (POST)
      await apiRequest(API_URL, {
        method: "POST",
        body: JSON.stringify({ nombre, direccion, ciudad }),
      });
      showAlert("Sede creada correctamente.", "success");
    }

    closeModal();
    await loadSedes();
  } catch (error) {
    showAlert(error.message);
  }
}

async function deactivateSede(sedeId) {
  if (!authToken) {
    return;
  }

  if (!window.confirm("Deseas desactivar esta sede?")) {
    return;
  }

  try {
    await apiRequest(`${API_URL}/${sedeId}`, {
      method: "DELETE",
    });

    showAlert("Sede desactivada correctamente.", "success");
    await loadSedes();
  } catch (error) {
    showAlert(error.message);
  }
}

tableBody.addEventListener("click", (event) => {
  const deactivateBtn = event.target.closest('[data-action="deactivate"]');
  if (deactivateBtn) {
    const sedeId = deactivateBtn.dataset.id;
    if (sedeId) {
      void deactivateSede(sedeId);
    }
    return;
  }

  const editBtn = event.target.closest('[data-action="edit"]');
  if (editBtn) {
    const sedeId = editBtn.dataset.id;
    const initialData = {
      nombre: editBtn.dataset.nombre,
      direccion: editBtn.dataset.direccion,
      ciudad: editBtn.dataset.ciudad,
    };
    openModal(sedeId, initialData);
  }
});

openModalBtn.addEventListener("click", () => openModal());
closeModalBtn.addEventListener("click", closeModal);
cancelModalBtn.addEventListener("click", closeModal);
modal.addEventListener("click", (event) => {
  if (event.target === modal) {
    closeModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && modal.classList.contains("is-open")) {
    closeModal();
  }
});

form.addEventListener("submit", (event) => {
  void submitSede(event);
});

void loadSedes();
