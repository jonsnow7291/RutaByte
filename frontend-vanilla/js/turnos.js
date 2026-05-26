const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";
const API_URL = `${API_BASE_URL.replace(/\/$/, "")}/cajero/turnos`;

const alertSlot = document.getElementById("alertSlot");
const noShiftView = document.getElementById("noShiftView");
const activeShiftView = document.getElementById("activeShiftView");

const lblFechaApertura = document.getElementById("lblFechaApertura");
const lblMontoApertura = document.getElementById("lblMontoApertura");
const lblSede = document.getElementById("lblSede");

// Modals & Forms
const aperturaModal = document.getElementById("aperturaModal");
const aperturaForm = document.getElementById("aperturaForm");
const cierreModal = document.getElementById("cierreModal");
const cierreForm = document.getElementById("cierreForm");
const justificacionField = document.getElementById("justificacionField");
const txtJustificacion = document.getElementById("justificacion");

// Buttons
const btnOpenAperturaModal = document.getElementById("btnOpenAperturaModal");
const btnOpenCierreModal = document.getElementById("btnOpenCierreModal");

const closeAperturaModalBtn = document.getElementById("closeAperturaModalBtn");
const cancelAperturaModalBtn = document.getElementById("cancelAperturaModalBtn");
const closeCierreModalBtn = document.getElementById("closeCierreModalBtn");
const cancelCierreModalBtn = document.getElementById("cancelCierreModalBtn");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

let activeShift = null;

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

function getHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  };
}

async function cargarTurnoActivo() {
  try {
    const response = await fetch(`${API_URL}/activo`, {
      method: "GET",
      headers: getHeaders(),
    });

    if (response.status === 404) {
      activeShift = null;
      mostrarVistaNoShift();
      return;
    }

    if (!response.ok) {
      throw new Error("Error al obtener el turno activo");
    }

    activeShift = await response.json();
    mostrarVistaShiftActivo(activeShift);
  } catch (error) {
    console.error(error);
    showAlert(error.message);
  }
}

function mostrarVistaNoShift() {
  activeShiftView.style.display = "none";
  noShiftView.style.display = "block";
}

async function cargarTransacciones() {
  const tableBody = document.getElementById("transaccionesTableBody");
  if (!tableBody) return;
  tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--muted);">Cargando transacciones...</td></tr>';

  try {
    const response = await fetch(`${API_URL}/transacciones`, {
      method: "GET",
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Error al obtener transacciones");
    }

    const transacciones = await response.json();
    if (!transacciones.length) {
      tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--muted);">No hay transacciones registradas en este turno.</td></tr>';
      return;
    }

    tableBody.innerHTML = transacciones.map((p) => {
      const date = new Date(p.creado_en);
      const subtotal = parseFloat(p.subtotal_base || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
      const impuesto = parseFloat(p.impuesto_total || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
      const total = parseFloat(p.monto_total || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

      return `
        <tr>
          <td>${date.toLocaleString("es-CO")}</td>
          <td><strong>#${p.pedido_id}</strong></td>
          <td><span class="tag tag--role">${p.metodo_pago}</span></td>
          <td>${subtotal}</td>
          <td>${impuesto}</td>
          <td><strong>${total}</strong></td>
        </tr>
      `;
    }).join("");
  } catch (error) {
    console.error(error);
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444;">Error cargando historial: ${error.message}</td></tr>`;
  }
}

function mostrarVistaShiftActivo(shift) {
  noShiftView.style.display = "none";
  activeShiftView.style.display = "block";

  const date = new Date(shift.fecha_apertura);
  lblFechaApertura.textContent = date.toLocaleString("es-ES");
  lblMontoApertura.textContent = `$${parseFloat(shift.monto_apertura).toLocaleString("es-ES", { minimumFractionDigits: 2 })}`;

  // Resolve sede name from sessionStorage if stored
  const userSedeId = sessionStorage.getItem("sede_id");
  lblSede.textContent = `Sede ID: ${userSedeId || shift.sede_id}`;

  // Load transactions list
  cargarTransacciones();
}

// Modal handling
btnOpenAperturaModal.addEventListener("click", () => {
  aperturaModal.classList.add("is-open");
});

closeAperturaModalBtn.addEventListener("click", () => {
  aperturaModal.classList.remove("is-open");
});
cancelAperturaModalBtn.addEventListener("click", () => {
  aperturaModal.classList.remove("is-open");
});

btnOpenCierreModal.addEventListener("click", () => {
  txtJustificacion.value = "";
  txtJustificacion.required = false;
  justificacionField.style.display = "none";
  cierreModal.classList.add("is-open");
});

closeCierreModalBtn.addEventListener("click", () => {
  cierreModal.classList.remove("is-open");
});
cancelCierreModalBtn.addEventListener("click", () => {
  cierreModal.classList.remove("is-open");
});

// Forms Submission
aperturaForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(aperturaForm);
  const rawApertura = String(formData.get("monto_apertura") || "0").replace(/\D/g, "");
  const data = {
    monto_apertura: parseFloat(rawApertura) || 0,
  };

  try {
    const response = await fetch(`${API_URL}/apertura`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Error al abrir el turno");
    }

    aperturaForm.reset();
    aperturaModal.classList.remove("is-open");
    showAlert("Turno de caja abierto correctamente", "success");
    await cargarTurnoActivo();
  } catch (error) {
    showAlert(error.message);
  }
});

cierreForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(cierreForm);
  const rawCierre = String(formData.get("monto_cierre_real") || "0").replace(/\D/g, "");
  const data = {
    monto_cierre_real: parseFloat(rawCierre) || 0,
    justificacion: formData.get("justificacion") || null,
  };

  try {
    const response = await fetch(`${API_URL}/cierre`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });

    if (response.status === 400) {
      const err = await response.json();
      if (err.detail && err.detail.includes("justificación")) {
        // Enforce discrepancy justification input
        justificacionField.style.display = "block";
        txtJustificacion.required = true;
        txtJustificacion.focus();
        showAlert("Se requiere una justificación por descuadre detectado entre lo físico y el sistema.", "error");
        return;
      }
      throw new Error(err.detail || "Error al cerrar el turno");
    }

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Error al cerrar el turno");
    }

    cierreForm.reset();
    cierreModal.classList.remove("is-open");
    showAlert("Turno de caja cerrado correctamente. Balance auditado con éxito.", "success");
    await cargarTurnoActivo();
  } catch (error) {
    showAlert(error.message);
  }
});

// Init load
if (authToken) {
  cargarTurnoActivo();
}

function setupCurrencyInput(input) {
  if (!input) return;
  input.type = "text";
  input.inputMode = "numeric";
  
  input.addEventListener("input", (e) => {
    let cursorPosition = e.target.selectionStart;
    const originalLength = e.target.value.length;
    const clean = e.target.value.replace(/\D/g, "");
    
    if (clean) {
      const formatted = clean.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      e.target.value = formatted;
      const newLength = e.target.value.length;
      cursorPosition = cursorPosition + (newLength - originalLength);
      e.target.setSelectionRange(cursorPosition, cursorPosition);
    } else {
      e.target.value = "";
    }
  });
}

// Bind listeners
const txtMontoApertura = document.getElementById("monto_apertura");
const txtMontoCierreReal = document.getElementById("monto_cierre_real");
setupCurrencyInput(txtMontoApertura);
setupCurrencyInput(txtMontoCierreReal);
