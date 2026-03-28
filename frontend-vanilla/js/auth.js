const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");
const submitButton = loginForm.querySelector("button[type=\"submit\"]");

function showError(message) {
  loginError.textContent = message;
}

function clearError() {
  loginError.textContent = "";
}

function decodeBase64Url(segment) {
  const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4 || 4)) % 4), "=");
  const binary = window.atob(padded);
  const utf8 = Array.from(binary, (character) =>
    `%${character.charCodeAt(0).toString(16).padStart(2, "0")}`,
  ).join("");

  return decodeURIComponent(utf8);
}

function decodeJwtPayload(token) {
  const parts = token.split(".");
  if (parts.length !== 3) {
    throw new Error("El token recibido no tiene un formato valido.");
  }

  return JSON.parse(decodeBase64Url(parts[1]));
}

function getRedirectPath(rolId) {
  const redirects = {
    1: "dashboard.html",
    2: "dashboard.html",
    3: "dashboard.html",
  };

  return redirects[Number(rolId)] ?? "dashboard.html";
}

async function login(event) {
  event.preventDefault();
  clearError();

  const correo = loginForm.correo.value.trim();
  const contrasena = loginForm.contrasena.value.trim();

  if (!correo || !contrasena) {
    showError("Completa el correo electronico y la contrasena.");
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Ingresando...";

  try {
    const API_BASE_URL = window.RUTABYTE_API_BASE_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ correo, contrasena }),
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.detail || payload.message || "No fue posible iniciar sesion.");
    }

    const token = payload.access_token || payload.token || payload.jwt;
    if (!token) {
      throw new Error("La respuesta de autenticacion no incluyo un JWT.");
    }

    sessionStorage.setItem("access_token", token);
    if (payload.token_type) {
      sessionStorage.setItem("token_type", payload.token_type);
    }

    const jwtPayload = decodeJwtPayload(token);
    const rolId = Number(jwtPayload.rol_id ?? jwtPayload.role_id);

    sessionStorage.setItem("correo", String(jwtPayload.correo ?? jwtPayload.sub ?? correo));
    sessionStorage.setItem("rol_id", String(rolId));
    sessionStorage.setItem("role_id", String(rolId));
    if (jwtPayload.sede_id !== undefined && jwtPayload.sede_id !== null) {
      sessionStorage.setItem("sede_id", String(jwtPayload.sede_id));
    }

    window.location.href = getRedirectPath(rolId);
  } catch (error) {
    showError(error.message);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Ingresar";
  }
}

loginForm.addEventListener("submit", login);
