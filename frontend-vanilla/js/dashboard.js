const authToken = window.RutaByteAuthGuard?.requireAuth?.();
const roleLabel = document.getElementById("dashboardRole");
const dashboardEmail = document.getElementById("dashboardEmail");
const logoutBtn = document.getElementById("logoutBtn");

const adminTile = document.getElementById("adminTile");
const adminUsuariosTile = document.getElementById("adminUsuariosTile");
const adminMesasTile = document.getElementById("adminMesasTile");
const adminProductosTile = document.getElementById("adminProductosTile");
const adminCategoriasTile = document.getElementById("adminCategoriasTile");
const adminAuditoriaTile = document.getElementById("adminAuditoriaTile");

const meseroTile = document.getElementById("meseroTile");

const cajeroInventarioTile = document.getElementById("cajeroInventarioTile");
const cajeroPagosTile = document.getElementById("cajeroPagosTile");
const cajeroTurnosTile = document.getElementById("cajeroTurnosTile");
const reportesTile = document.getElementById("reportesTile");

function getStoredValue(keys) {
  for (const key of keys) {
    const value = sessionStorage.getItem(key);
    if (value) {
      return value;
    }
  }
  return null;
}

function getRoleName(roleId) {
  const roleNames = {
    1: "ADMIN",
    2: "CAJERO",
    3: "MESERO",
  };

  return roleNames[Number(roleId)] ?? "USUARIO";
}

function applyRoleUi() {
  const roleId = Number(getStoredValue(["rol_id", "role_id"]));
  const email = getStoredValue(["correo", "sub", "email"]);
  const roleName = getRoleName(roleId);

  roleLabel.textContent = roleName;
  dashboardEmail.textContent = email || "Usuario autenticado";

  if (Number(roleId) !== 1) {
    adminTile.style.display = "none";
    adminUsuariosTile.style.display = "none";
    adminProductosTile.style.display = "none";
    if (adminCategoriasTile) adminCategoriasTile.style.display = "none";
    if (adminMesasTile) adminMesasTile.style.display = "none";
    if (adminAuditoriaTile) adminAuditoriaTile.style.display = "none";
  }

  if (roleId !== 3) {
    if (meseroTile) meseroTile.style.display = "none";
  }

  if (![1, 2].includes(roleId)) {
    if (cajeroInventarioTile) cajeroInventarioTile.style.display = "none";
    if (cajeroPagosTile) cajeroPagosTile.style.display = "none";
    if (cajeroTurnosTile) cajeroTurnosTile.style.display = "none";
    if (reportesTile) reportesTile.style.display = "none";
  }
}

const API_BASE_URL = window.RUTABYTE_API_BASE_URL || document.body?.dataset.apiBaseUrl || "http://127.0.0.1:8000";

function logout(event) {
  event.preventDefault();
  sessionStorage.clear();
  window.location.href = "index.html";
}

function connectNotifications() {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${wsProtocol}//${API_BASE_URL.replace(/^https?:\/\//, "")}/ws/pedidos?token=${authToken}`;

  const socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.evento === "REPORTE_MASIVO_COMPLETO") {
        showToast(data.mensaje, "success", data.archivo_url);
      } else if (data.evento === "PAGO_PROCESADO") {
        showToast(data.mensaje, "success");
      } else if (data.evento === "ALERTA_STOCK_BAJO") {
        showToast(data.mensaje, "error");
      }
    } catch (e) {
      console.error(e);
    }
  };

  socket.onclose = () => {
    setTimeout(connectNotifications, 5000); // Auto reconnect
  };
}

function showToast(message, type = "success", actionUrl = null) {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.style.position = "fixed";
    container.style.bottom = "24px";
    container.style.right = "24px";
    container.style.zIndex = "9999";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "12px";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.style.background = type === "success" ? "rgba(22, 163, 74, 0.9)" : "rgba(220, 38, 38, 0.9)";
  toast.style.color = "#ffffff";
  toast.style.padding = "16px 24px";
  toast.style.borderRadius = "12px";
  toast.style.boxShadow = "0 8px 32px 0 rgba(0, 0, 0, 0.15)";
  toast.style.backdropFilter = "blur(8px)";
  toast.style.fontFamily = "system-ui, sans-serif";
  toast.style.fontSize = "14px";
  toast.style.fontWeight = "500";
  toast.style.transition = "all 0.3s ease";
  toast.style.transform = "translateY(50px)";
  toast.style.opacity = "0";

  let content = `<div>${message}</div>`;
  if (actionUrl) {
    content += `<a class="btn btn-ghost" href="${actionUrl}" style="margin-top: 8px; display: inline-block; color: white; border: 1px solid white; text-decoration: none; padding: 4px 8px; border-radius: 4px;" download>Descargar Reporte</a>`;
  }

  toast.innerHTML = content;
  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.style.transform = "translateY(0)";
    toast.style.opacity = "1";
  }, 10);

  // Remove after 6 seconds
  setTimeout(() => {
    toast.style.transform = "translateY(-50px)";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 6000);
}

if (authToken) {
  applyRoleUi();
  connectNotifications();
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", logout);
}