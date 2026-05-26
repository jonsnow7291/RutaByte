from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.categoria import Categoria
from app.models.detalle_pedido import DetallePedido
from app.models.inventario import Inventario
from app.models.mesa import Mesa
from app.models.pago import Pago
from app.models.pedido import Pedido
from app.models.producto import Producto
from app.models.rol import Rol
from app.models.sede import Sede
from app.models.usuario import Usuario


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


@dataclass(frozen=True)
class SeedUser:
    correo: str
    nombre: str
    password: str
    rol_nombre: str
    sede_nombre: str | None = None


DEFAULT_ROLES = ("ADMIN", "CAJERO", "MESERO")
DEFAULT_SEDE = {
    "nombre": "Sede Principal",
    "direccion": "Calle 1 # 1-1",
    "ciudad": "Bogota",
}
DEFAULT_SEDES = (
    DEFAULT_SEDE,
    {"nombre": "Sede Norte", "direccion": "Carrera 15 # 100-20", "ciudad": "Bogota"},
    {"nombre": "Sede Sur", "direccion": "Avenida 68 # 35-40 Sur", "ciudad": "Bogota"},
    {"nombre": "Sede Centro", "direccion": "Calle 19 # 7-45", "ciudad": "Bogota"},
)
DEFAULT_USERS = (
    SeedUser(
        correo="admin@rutabyte.local",
        nombre="Administrador Principal",
        password="Admin123!",
        rol_nombre="ADMIN",
    ),
    SeedUser(
        correo="cajero@rutabyte.local",
        nombre="Cajero Principal",
        password="Cajero123!",
        rol_nombre="CAJERO",
        sede_nombre="Sede Principal",
    ),
    SeedUser(
        correo="mesero@rutabyte.local",
        nombre="Mesero Principal",
        password="Mesero123!",
        rol_nombre="MESERO",
        sede_nombre="Sede Principal",
    ),
    SeedUser(
        correo="admin.operaciones@rutabyte.local",
        nombre="Administrador de Operaciones",
        password="Admin123!",
        rol_nombre="ADMIN",
    ),
    SeedUser(
        correo="admin.reportes@rutabyte.local",
        nombre="Administrador de Reportes",
        password="Admin123!",
        rol_nombre="ADMIN",
    ),
    SeedUser(
        correo="cajero.norte@rutabyte.local",
        nombre="Cajero Sede Norte",
        password="Cajero123!",
        rol_nombre="CAJERO",
        sede_nombre="Sede Norte",
    ),
    SeedUser(
        correo="cajero.sur@rutabyte.local",
        nombre="Cajero Sede Sur",
        password="Cajero123!",
        rol_nombre="CAJERO",
        sede_nombre="Sede Sur",
    ),
    SeedUser(
        correo="cajero.centro@rutabyte.local",
        nombre="Cajero Sede Centro",
        password="Cajero123!",
        rol_nombre="CAJERO",
        sede_nombre="Sede Centro",
    ),
    SeedUser(
        correo="mesero.norte@rutabyte.local",
        nombre="Mesero Sede Norte",
        password="Mesero123!",
        rol_nombre="MESERO",
        sede_nombre="Sede Norte",
    ),
    SeedUser(
        correo="mesero.sur@rutabyte.local",
        nombre="Mesero Sede Sur",
        password="Mesero123!",
        rol_nombre="MESERO",
        sede_nombre="Sede Sur",
    ),
    SeedUser(
        correo="mesero.centro@rutabyte.local",
        nombre="Mesero Sede Centro",
        password="Mesero123!",
        rol_nombre="MESERO",
        sede_nombre="Sede Centro",
    ),
    SeedUser(
        correo="mesero.apoyo@rutabyte.local",
        nombre="Mesero de Apoyo",
        password="Mesero123!",
        rol_nombre="MESERO",
        sede_nombre="Sede Principal",
    ),
)

DEMO_REFERENCE = "DEMO-HISTORICO-RUTABYTE"
DEMO_CATEGORIES = ("Bebidas", "Platos Fuertes", "Entradas", "Postres")
DEMO_PRODUCTS = (
    ("DEMO-CAF-01", "Bebidas", "Cafe Americano", "5200.00", "1800.00", "5.00", 18),
    ("DEMO-CAP-02", "Bebidas", "Capuchino", "7800.00", "2800.00", "5.00", 16),
    ("DEMO-JUG-03", "Bebidas", "Jugo Natural", "8600.00", "3100.00", "5.00", 14),
    ("DEMO-LIM-04", "Bebidas", "Limonada", "7200.00", "2500.00", "5.00", 12),
    ("DEMO-HAM-05", "Platos Fuertes", "Hamburguesa Ruta", "28500.00", "12600.00", "19.00", 10),
    ("DEMO-PAS-06", "Platos Fuertes", "Pasta Alfredo", "26800.00", "11200.00", "19.00", 10),
    ("DEMO-POL-07", "Platos Fuertes", "Pollo Grillado", "31200.00", "14300.00", "19.00", 9),
    ("DEMO-ENS-08", "Platos Fuertes", "Ensalada Cesar", "23800.00", "9200.00", "19.00", 8),
    ("DEMO-EMP-09", "Entradas", "Empanadas Mixtas", "13200.00", "5200.00", "5.00", 20),
    ("DEMO-PAP-10", "Entradas", "Papas Rusticas", "14800.00", "6100.00", "5.00", 18),
    ("DEMO-ALA-11", "Entradas", "Alitas BBQ", "22600.00", "9800.00", "19.00", 12),
    ("DEMO-SOP-12", "Entradas", "Sopa del Dia", "12800.00", "4700.00", "5.00", 9),
    ("DEMO-BRO-13", "Postres", "Brownie con Helado", "14200.00", "5600.00", "19.00", 8),
    ("DEMO-FLA-14", "Postres", "Flan de Caramelo", "9800.00", "3600.00", "5.00", 10),
    ("DEMO-TIR-15", "Postres", "Tiramisu", "16800.00", "7100.00", "19.00", 6),
    ("DEMO-QUE-16", "Postres", "Cheesecake", "15400.00", "6400.00", "19.00", 7),
    ("DEMO-PIZ-17", "Platos Fuertes", "Pizza Personal", "24800.00", "10800.00", "19.00", 10),
    ("DEMO-TAC-18", "Platos Fuertes", "Tacos Ruta", "21400.00", "8900.00", "19.00", 11),
    ("DEMO-TEQ-19", "Entradas", "Tequenos", "11800.00", "4300.00", "5.00", 15),
    ("DEMO-ARO-20", "Entradas", "Aros de Cebolla", "12600.00", "4900.00", "5.00", 14),
    ("DEMO-MAL-21", "Bebidas", "Malteada", "13800.00", "5600.00", "19.00", 9),
    ("DEMO-TEF-22", "Bebidas", "Te Frio", "6800.00", "2200.00", "5.00", 12),
    ("DEMO-HEL-23", "Postres", "Helado Artesanal", "11200.00", "4200.00", "19.00", 8),
    ("DEMO-GAL-24", "Postres", "Galleta de Chocolate", "6200.00", "2100.00", "5.00", 20),
)
DEMO_PAYMENT_METHODS = ("EFECTIVO", "TARJETA", "MIXTO")


def _get_role_by_name(db: Session, role_name: str) -> Rol | None:
    return db.scalar(select(Rol).where(func.lower(Rol.nombre) == role_name.lower()))


def _get_user_by_email(db: Session, correo: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(func.lower(Usuario.correo) == correo.lower()))


def _get_sede_by_name(db: Session, sede_name: str) -> Sede | None:
    return db.scalar(select(Sede).where(func.lower(Sede.nombre) == sede_name.lower()))


def _get_category_by_name(db: Session, category_name: str) -> Categoria | None:
    return db.scalar(select(Categoria).where(func.lower(Categoria.nombre) == category_name.lower()))


def _get_product_by_code(db: Session, code: str) -> Producto | None:
    return db.scalar(select(Producto).where(Producto.codigo == code))


def _get_mesa_by_identifier(db: Session, sede_id: int, identifier: str) -> Mesa | None:
    return db.scalar(
        select(Mesa).where(
            Mesa.sede_id == sede_id,
            func.lower(Mesa.identificador_mesa) == identifier.lower(),
        )
    )


def _seed_demo_catalog(db: Session, sede: Sede) -> tuple[list[Producto], list[Mesa]]:
    categories_by_name: dict[str, Categoria] = {}
    for category_name in DEMO_CATEGORIES:
        category = _get_category_by_name(db, category_name)
        if category is None:
            category = Categoria(nombre=category_name, activa=True)
            db.add(category)
            db.flush()
        categories_by_name[category_name] = category

    products: list[Producto] = []
    for code, category_name, name, price, cost, tax, threshold in DEMO_PRODUCTS:
        product = _get_product_by_code(db, code)
        if product is None:
            product = Producto(
                categoria_id=categories_by_name[category_name].id,
                codigo=code,
                nombre=name,
                descripcion=f"Producto demo para reportes: {name}",
                precio=Decimal(price),
                costo_compra=Decimal(cost),
                impuesto_iva=Decimal(tax),
                umbral_minimo=threshold,
                activo=True,
            )
            db.add(product)
            db.flush()
        products.append(product)

        inventory = db.scalar(
            select(Inventario).where(
                Inventario.sede_id == sede.id,
                Inventario.producto_id == product.id,
            )
        )
        if inventory is None:
            stock = 3 if code in {"DEMO-TIR-15", "DEMO-QUE-16", "DEMO-SOP-12"} else 80 + (product.id % 7) * 12
            inventory = Inventario(
                sede_id=sede.id,
                producto_id=product.id,
                stock=stock,
                umbral_minimo=threshold,
            )
            db.add(inventory)

    tables: list[Mesa] = []
    for index in range(1, 9):
        identifier = f"Demo {index:02d}"
        table = _get_mesa_by_identifier(db, sede.id, identifier)
        if table is None:
            table = Mesa(
                sede_id=sede.id,
                identificador_mesa=identifier,
                estado="LIBRE",
                activa=True,
            )
            db.add(table)
            db.flush()
        tables.append(table)

    db.flush()
    return products, tables


def _seed_demo_report_data(db: Session, sede: Sede, cajero: Usuario, mesero: Usuario) -> None:
    reference = f"{DEMO_REFERENCE}-SEDE-{sede.id}"
    existing_references = [reference]
    if sede.nombre == DEFAULT_SEDE["nombre"]:
        existing_references.append(DEMO_REFERENCE)
    existing_demo_payment = db.scalar(select(Pago.id).where(Pago.referencia.in_(existing_references)).limit(1))
    if existing_demo_payment is not None:
        return

    products, tables = _seed_demo_catalog(db, sede)
    now = datetime.now().replace(microsecond=0, second=0)
    order_count = 0

    for days_ago in range(120, -1, -1):
        sale_date = now - timedelta(days=days_ago)
        daily_orders = 5 + (days_ago % 5)
        if sale_date.weekday() in (4, 5):
            daily_orders += 3

        for daily_index in range(daily_orders):
            created_at = sale_date.replace(
                hour=10 + ((daily_index * 2) % 12),
                minute=(daily_index * 11 + days_ago) % 60,
            )
            table = tables[(days_ago + daily_index) % len(tables)]
            item_count = 2 + ((days_ago + daily_index) % 3)
            selected_products = [
                products[(days_ago * 3 + daily_index * 5 + offset * 4) % len(products)]
                for offset in range(item_count)
            ]

            pedido = Pedido(
                mesa_id=table.id,
                usuario_id=mesero.id,
                estado="PAGADO",
                descuento=Decimal("0.00"),
                creado_en=created_at,
            )
            db.add(pedido)
            db.flush()

            subtotal = Decimal("0.00")
            tax_total = Decimal("0.00")
            for offset, product in enumerate(selected_products):
                quantity = 1 + ((days_ago + daily_index + offset) % 4)
                line_base = Decimal(quantity) * product.precio
                line_tax = line_base * (Decimal(str(product.impuesto_iva or 0)) / Decimal("100"))
                subtotal += line_base
                tax_total += line_tax
                db.add(
                    DetallePedido(
                        pedido_id=pedido.id,
                        producto_id=product.id,
                        cantidad=quantity,
                        precio_unitario=product.precio,
                        costo_unitario=product.costo_compra,
                        precio_base=product.precio,
                        impuesto_iva_total=line_tax,
                        notas="Venta historica demo",
                    )
                )

            method = DEMO_PAYMENT_METHODS[(days_ago + daily_index) % len(DEMO_PAYMENT_METHODS)]
            total = subtotal + tax_total
            cash = total if method == "EFECTIVO" else None
            card = total if method == "TARJETA" else None
            if method == "MIXTO":
                cash = (total * Decimal("0.45")).quantize(Decimal("0.01"))
                card = total - cash

            db.add(
                Pago(
                    pedido_id=pedido.id,
                    usuario_id=cajero.id,
                    metodo_pago=method,
                    monto_total=total,
                    subtotal_base=subtotal,
                    impuesto_total=tax_total,
                    monto_efectivo=cash,
                    monto_tarjeta=card,
                    referencia=reference,
                    comprobante=f"COMPROBANTE DEMO #{pedido.id} - Total: {total}",
                    creado_en=created_at,
                )
            )
            table.estado = "LIBRE"
            order_count += 1

            if order_count % 100 == 0:
                db.flush()


def seed_initial_data(db: Session) -> None:
    roles_by_name: dict[str, Rol] = {}
    for role_name in DEFAULT_ROLES:
        rol = _get_role_by_name(db, role_name)
        if rol is None:
            rol = Rol(nombre=role_name, activo=True)
            db.add(rol)
            db.flush()
        roles_by_name[role_name] = rol

    sedes_by_name: dict[str, Sede] = {}
    for sede_data in DEFAULT_SEDES:
        sede = _get_sede_by_name(db, sede_data["nombre"])
        if sede is None:
            sede = Sede(**sede_data)
            db.add(sede)
            db.flush()
        sedes_by_name[sede_data["nombre"]] = sede

    sede_principal = sedes_by_name[DEFAULT_SEDE["nombre"]]
    password_hashes: dict[str, str] = {}

    for seed_user in DEFAULT_USERS:
        usuario = _get_user_by_email(db, seed_user.correo)
        if usuario is not None:
            continue

        if seed_user.password not in password_hashes:
            password_hashes[seed_user.password] = pwd_context.hash(seed_user.password)

        db.add(
            Usuario(
                rol_id=roles_by_name[seed_user.rol_nombre].id,
                sede_id=None if seed_user.sede_nombre is None else sedes_by_name[seed_user.sede_nombre].id,
                nombre=seed_user.nombre,
                correo=seed_user.correo,
                hash_contrasena=password_hashes[seed_user.password],
                activo=True,
            )
        )

    db.flush()
    demo_pairs = (
        ("Sede Principal", "cajero@rutabyte.local", "mesero@rutabyte.local"),
        ("Sede Norte", "cajero.norte@rutabyte.local", "mesero.norte@rutabyte.local"),
        ("Sede Sur", "cajero.sur@rutabyte.local", "mesero.sur@rutabyte.local"),
        ("Sede Centro", "cajero.centro@rutabyte.local", "mesero.centro@rutabyte.local"),
    )
    for sede_name, cajero_email, mesero_email in demo_pairs:
        cajero = _get_user_by_email(db, cajero_email)
        mesero = _get_user_by_email(db, mesero_email)
        if cajero is not None and mesero is not None:
            _seed_demo_report_data(db, sedes_by_name[sede_name], cajero, mesero)

    db.commit()
