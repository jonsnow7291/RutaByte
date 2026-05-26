from __future__ import annotations

import os
from datetime import datetime


def _log_email(to_email: str, subject: str, body: str) -> None:
    # Build absolute path to email_logs.txt in workspace root
    # Since this file runs under app/core/email.py, the root is two directories up (app/../..)
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file_path = os.path.join(root_dir, "email_logs.txt")

    log_entry = (
        f"========================================================================\n"
        f"📧 EMAIL ENVIADO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"------------------------------------------------------------------------\n"
        f"Para:      {to_email}\n"
        f"Asunto:    {subject}\n"
        f"------------------------------------------------------------------------\n"
        f"{body}\n"
        f"========================================================================\n\n"
    )

    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"[Email Service] Email sent successfully to {to_email} (Logged to email_logs.txt)")
    except Exception as exc:
        print(f"[Email Service] Error logging email to {log_file_path}: {exc}")


def send_credentials_email(to_email: str, nombre: str, contrasena: str) -> None:
    subject = "¡Bienvenido a RutaByte! - Tus credenciales de acceso iniciales"
    body = (
        f"Hola {nombre},\n\n"
        f"Te damos la bienvenida al sistema RutaByte. Se ha creado tu cuenta con los siguientes detalles:\n\n"
        f"• Correo electrónico: {to_email}\n"
        f"• Contraseña inicial:  {contrasena}\n\n"
        f"Por seguridad, te recomendamos cambiar tu contraseña una vez que inicies sesión en la plataforma.\n\n"
        f"Atentamente,\n"
        f"El equipo de administración de RutaByte"
    )
    _log_email(to_email, subject, body)


def send_recovery_email(to_email: str, nombre: str, token: str, api_base_url: str = "http://127.0.0.1:8000") -> None:
    subject = "RutaByte - Recuperación de credenciales"
    # Create reset link referencing recovering.html in frontend
    # Since frontend is served at port 5500 or standard static index, we can generate a generic reset link
    reset_link = f"http://127.0.0.1:5500/recuperar.html?token={token}"
    body = (
        f"Hola {nombre},\n\n"
        f"Hemos recibido una solicitud para restablecer tu contraseña en el sistema RutaByte.\n"
        f"Para proceder con el cambio, por favor haz clic en el siguiente enlace (válido por 15 minutos):\n\n"
        f"{reset_link}\n\n"
        f"Si prefieres ingresar el token manualmente, utiliza el siguiente código:\n"
        f"Token: {token}\n\n"
        f"Si no has solicitado esta acción, puedes ignorar este correo de forma segura.\n\n"
        f"Atentamente,\n"
        f"El equipo de soporte de RutaByte"
    )
    _log_email(to_email, subject, body)
