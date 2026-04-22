document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const loginError = document.getElementById("loginError");
  const submitButton = document.getElementById("loginBtn");
  const correoInput = document.getElementById("correo");
  const contrasenaInput = document.getElementById("contrasena");

  let isSubmitting = false;
  let loginCompleted = false;

  if (!loginForm || !loginError || !submitButton || !correoInput || !contrasenaInput) {
    console.error("No se encontro el formulario de login o sus elementos.");
    return;
  }

  function showError(message) {
    loginError.textContent = message;
  }

  function clearError() {
    loginError.textContent = "";
  }

  async function login(event) {
    event.preventDefault();

    if (isSubmitting || loginCompleted) {
      return;
    }

    clearError();

    const correo = correoInput.value.trim();
    const contrasena = contrasenaInput.value.trim();

    if (!correo || !contrasena) {
      showError("Completa el correo electronico y la contrasena.");
      return;
    }

    isSubmitting = true;
    submitButton.disabled = true;
    submitButton.textContent = "Ingresando...";

    try {
      const API_BASE_URL =
        window.RUTABYTE_API_BASE_URL ||
        document.body?.dataset.apiBaseUrl ||
        "http://127.0.0.1:8000";

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ correo, contrasena }),
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          payload.detail || payload.message || "No fue posible iniciar sesion."
        );
      }

      const token = payload.access_token || payload.token || payload.jwt;
      if (!token) {
        throw new Error("La respuesta de autenticacion no incluyo un JWT.");
      }

      sessionStorage.setItem("access_token", token);
      sessionStorage.setItem("token_type", payload.token_type || "bearer");
      sessionStorage.setItem("correo", correo);
      sessionStorage.setItem("rol_id", "1");
      sessionStorage.setItem("role_id", "1");

      loginCompleted = true;

      submitButton.disabled = true;
      submitButton.textContent = "Redirigiendo...";

      window.location.replace("/frontend-vanilla/dashboard.html");
    } catch (error) {
      console.error("Error login:", error);
      showError(error.message || "Error al iniciar sesion.");
      isSubmitting = false;
      submitButton.disabled = false;
      submitButton.textContent = "Ingresar";
    }
  }

  loginForm.addEventListener("submit", login);
});