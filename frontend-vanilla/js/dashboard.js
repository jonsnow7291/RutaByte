const authToken = window.RutaByteAuthGuard?.requireAuth?.();
const roleLabel = document.getElementById("dashboardRole");
const dashboardEmail = document.getElementById("dashboardEmail");
const logoutBtn = document.getElementById("logoutBtn");
const adminTile = document.getElementById("adminTile");
const adminUsuariosTile = document.getElementById("adminUsuariosTile");
const adminProductosTile = document.getElementById("adminProductosTile");
const meseroTile = document.getElementById("meseroTile");

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
  const roleId = getStoredValue(["rol_id", "role_id"]);
  const email = getStoredValue(["correo", "sub", "email"]);
  const roleName = getRoleName(roleId);

  roleLabel.textContent = roleName;
  dashboardEmail.textContent = email || "Usuario autenticado";

  if (Number(roleId) !== 1) {
    adminTile.style.display = "none";
    adminUsuariosTile.style.display = "none";
    adminProductosTile.style.display = "none";
  }

  if (Number(roleId) !== 3) {
    meseroTile.style.display = "none";
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

logoutBtn.addEventListener("click", logout);
