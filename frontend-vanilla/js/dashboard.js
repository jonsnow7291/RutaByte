const authToken = window.RutaByteAuthGuard?.requireAuth?.();
const roleLabel = document.getElementById("dashboardRole");
const dashboardEmail = document.getElementById("dashboardEmail");
const logoutBtn = document.getElementById("logoutBtn");

const adminTile = document.getElementById("adminTile");
const adminUsuariosTile = document.getElementById("adminUsuariosTile");
const adminMesasTile = document.getElementById("adminMesasTile");
const adminProductosTile = document.getElementById("adminProductosTile");

const meseroTile = document.getElementById("meseroTile");

const cajeroInventarioTile = document.getElementById("cajeroInventarioTile");
const cajeroPagosTile = document.getElementById("cajeroPagosTile");
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
    if (adminMesasTile) adminMesasTile.style.display = "none";
  }

  if (roleId !== 3) {
    if (meseroTile) meseroTile.style.display = "none";
  }

  if (![1, 2].includes(roleId)) {
    if (cajeroInventarioTile) cajeroInventarioTile.style.display = "none";
    if (cajeroPagosTile) cajeroPagosTile.style.display = "none";
    if (reportesTile) reportesTile.style.display = "none";
  }
}

function logout(event) {
  event.preventDefault();
  sessionStorage.clear();
  window.location.href = "index.html";
}

if (authToken) {
  applyRoleUi();
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", logout);
}