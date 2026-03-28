CREATE DATABASE rutaByte;
USE rutaByte;
-- Creación de tabla ROLES
CREATE TABLE ROLES (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    activo BOOLEAN DEFAULT TRUE
);

-- Creación de tabla SEDES
CREATE TABLE SEDES (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(255),
    ciudad VARCHAR(100),
    activa BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Creación de tabla USUARIOS
CREATE TABLE USUARIOS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rol_id INT NOT NULL,
    sede_id INT,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    hash_contrasena VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rol_id) REFERENCES ROLES(id),
    FOREIGN KEY (sede_id) REFERENCES SEDES(id)
);

-- Creación de tabla CATEGORIAS
CREATE TABLE CATEGORIAS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    activa BOOLEAN DEFAULT TRUE
);

-- Creación de tabla PRODUCTOS
CREATE TABLE PRODUCTOS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL,
    url_imagen VARCHAR(500),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES CATEGORIAS(id),
    CHECK (precio >= 0)
);

-- Creación de tabla HISTORIAL_PRECIOS
CREATE TABLE HISTORIAL_PRECIOS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    precio_anterior DECIMAL(10,2) NOT NULL,
    precio_nuevo DECIMAL(10,2) NOT NULL,
    cambiado_por INT NOT NULL,
    cambiado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES PRODUCTOS(id),
    FOREIGN KEY (cambiado_por) REFERENCES USUARIOS(id),
    CHECK (precio_anterior >= 0),
    CHECK (precio_nuevo >= 0)
);

-- Creación de tabla MESAS
CREATE TABLE MESAS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sede_id INT NOT NULL,
    identificador_mesa VARCHAR(50) NOT NULL,
    estado VARCHAR(20) DEFAULT 'LIBRE',
    activa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (sede_id) REFERENCES SEDES(id),
    UNIQUE (sede_id, identificador_mesa),
    CHECK (estado IN ('LIBRE', 'OCUPADA'))
);

-- Creación de tabla PEDIDOS
CREATE TABLE PEDIDOS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mesa_id INT NOT NULL,
    usuario_id INT NOT NULL,
    estado VARCHAR(50) DEFAULT 'EN_PREPARACION',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mesa_id) REFERENCES MESAS(id),
    FOREIGN KEY (usuario_id) REFERENCES USUARIOS(id),
    CHECK (estado IN ('EN_PREPARACION', 'LISTO', 'ENTREGADO'))
);

-- Creación de tabla DETALLE_PEDIDOS
CREATE TABLE DETALLE_PEDIDOS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    notas VARCHAR(150),
    FOREIGN KEY (pedido_id) REFERENCES PEDIDOS(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES PRODUCTOS(id),
    CHECK (cantidad > 0),
    CHECK (precio_unitario >= 0)
);

-- Creación de tabla REGISTROS_AUDITORIA
CREATE TABLE REGISTROS_AUDITORIA (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    tipo_evento VARCHAR(50) NOT NULL,
    direccion_ip VARCHAR(45),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES USUARIOS(id) ON DELETE SET NULL,
    CHECK (tipo_evento IN ('LOGIN_EXITOSO', 'LOGIN_FALLIDO'))
);

-- Datos iniciales sugeridos
INSERT IGNORE INTO ROLES (id, nombre, activo) VALUES
(1, 'ADMIN', TRUE),
(2, 'CAJERO', TRUE),
(3, 'MESERO', TRUE);

INSERT IGNORE INTO SEDES (id, nombre, direccion, ciudad, activa) VALUES
(1, 'Sede Principal', 'Calle 1 # 1-1', 'Bogota', TRUE);

-- Usuarios iniciales
-- Se crean con el script backend-fastapi/scripts/seed_initial_data.py
-- Credenciales por defecto:
-- admin@rutabyte.local / Admin123!
-- cajero@rutabyte.local / Cajero123!
-- mesero@rutabyte.local / Mesero123!
