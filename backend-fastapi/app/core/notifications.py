from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Store connections as tuples: (WebSocket, role_id)
        self.active_connections: list[tuple[WebSocket, int]] = []

    async def connect(self, websocket: WebSocket, role_id: int = 0) -> None:
        await websocket.accept()
        self.active_connections.append((websocket, role_id))
        print(f"[WebSocket] Nueva conexion establecida (Rol: {role_id}). Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections = [item for item in self.active_connections if item[0] != websocket]
        print(f"[WebSocket] Conexion cerrada. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        for connection, _ in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                print(f"[WebSocket] Error enviando mensaje: {exc}")

    async def broadcast_to_role(self, role_id: int, message: dict) -> None:
        for connection, r_id in self.active_connections:
            if r_id == role_id:
                try:
                    await connection.send_json(message)
                except Exception as exc:
                    print(f"[WebSocket] Error enviando mensaje a rol {role_id}: {exc}")


notification_manager = ConnectionManager()
