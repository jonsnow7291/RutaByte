const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";

const MESAS_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/mesas`;
const SEDES_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/sedes`;

const tableBody = document.getElementById("mesasTableBody");
const modal = document.getElementById("mesaModal");
const form = document.getElementById("mesaForm");

const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");

const sedeSelect = document.getElementById("sede_id");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

// 🔹 Estado global
let editandoMesaId = null;
let sedesCache = [];

// 🔹 Alert simple
function showAlert(message) {
  alert(message);
}

// 🔹 Modal
function openModal() {
  modal.classList.add("is-open");
}

function closeModal() {
  modal.classList.remove("is-open");
  form.reset();
  editandoMesaId = null;
}

// 🔹 API
async function apiRequest(url, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${authToken}`);
  headers.set("Content-Type", "application/json");

  const res = await fetch(url, { ...options, headers });
  const data = await res.json();

  if (!res.ok) throw new Error(data.detail || "Error");

  return data;
}

// 🔹 Obtener nombre de sede
function getSedeNombre(id) {
  const sede = sedesCache.find(s => s.id === id);
  return sede ? sede.nombre : id;
}

// 🔹 Cargar sedes
async function loadSedes() {
  try {
    const sedes = await apiRequest(SEDES_URL);

    sedesCache = sedes;

    sedeSelect.innerHTML = `<option value="">Seleccionar sede</option>`;

    sedes.forEach(s => {
      sedeSelect.innerHTML += `
        <option value="${s.id}">${s.nombre}</option>
      `;
    });

  } catch (err) {
    showAlert(err.message);
  }
}

// 🔹 Cargar mesas
async function loadMesas() {
  try {
    tableBody.innerHTML = `<tr><td colspan="5">Cargando...</td></tr>`;

    const mesas = await apiRequest(MESAS_URL);

    if (!mesas.length) {
      tableBody.innerHTML = `
        <tr><td colspan="5">No hay mesas registradas</td></tr>
      `;
      return;
    }

    tableBody.innerHTML = mesas.map(m => `
      <tr>
        <td>${getSedeNombre(m.sede_id)}</td>
        <td>${m.identificador_mesa}</td>
        <td>${m.estado}</td>
        <td>${m.activa ? "Activa" : "Inactiva"}</td>
        <td>
          <button onclick="editarMesa(${m.id}, '${m.identificador_mesa}', ${m.sede_id})">
            Editar
          </button>
          <button onclick="eliminarMesa(${m.id})">
            Eliminar
          </button>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    showAlert(err.message);
  }
}

// 🔹 Crear / Editar
async function createMesa(e) {
  e.preventDefault();

  const data = {
    sede_id: Number(form.sede_id.value),
    identificador_mesa: form.identificador.value.trim()
  };

  try {
    if (editandoMesaId) {
      // ✏️ EDITAR
      await apiRequest(`${MESAS_URL}/${editandoMesaId}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });

      showAlert("Mesa actualizada");
    } else {
      // ➕ CREAR
      await apiRequest(MESAS_URL, {
        method: "POST",
        body: JSON.stringify(data)
      });

      showAlert("Mesa creada");
    }

    closeModal();
    loadMesas();

  } catch (err) {
    showAlert(err.message);
  }
}

// 🔹 Editar (llenar form)
function editarMesa(id, identificador, sede_id) {
  editandoMesaId = id;

  form.identificador.value = identificador;
  form.sede_id.value = sede_id;

  openModal();
}

// 🔹 Eliminar (desactivar)
async function eliminarMesa(id) {
  if (!confirm("¿Seguro que quieres eliminar esta mesa?")) return;

  try {
    await apiRequest(`${MESAS_URL}/${id}`, {
      method: "DELETE"
    });

    showAlert("Mesa eliminada");
    loadMesas();

  } catch (err) {
    showAlert(err.message);
  }
}

// 🔹 Eventos
if (form) form.addEventListener("submit", createMesa);

if (openModalBtn) {
  openModalBtn.addEventListener("click", async () => {
    await loadSedes();
    openModal();
  });
}

if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
if (cancelModalBtn) cancelModalBtn.addEventListener("click", closeModal);

// 🔹 Init
if (authToken) {
  (async () => {
    await loadSedes();
    loadMesas();
  })();
}