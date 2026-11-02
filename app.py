import math
import calendar
from datetime import date, datetime
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from db import conectar, crear_tablas
from servicios import obtener_dolar, obtener_oficial

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

crear_tablas()
CATEGORIAS = ["Sueldo", "Alimentos", "Transporte", "Vivienda", "Servicios", "Salud", "Ocio", "Otros"]

@app.route("/")
def inicio():
    if "usuario_id" in session:
        return redirect(url_for("panel"))
    return redirect(url_for("login"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    errores = []

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        repetir = request.form.get("repetir", "")

        if "@" not in email or "." not in email:
            errores.append("Ingresá un email válido.")
        if len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if password != repetir:
            errores.append("Las contraseñas no coinciden.")

        if not errores:
            conexion = conectar()
            try:
                conexion.execute(
                    "INSERT INTO usuarios (email, password_hash) VALUES (?, ?)",
                    (email, generate_password_hash(password)),
                )
                conexion.commit()
                flash("Cuenta creada. Ya podés iniciar sesión.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                errores.append("Ese email ya está registrado.")
            finally:
                conexion.close()

    return render_template("registro.html", errores=errores)


@app.route("/login", methods=["GET", "POST"])
def login():
    errores = []

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conexion = conectar()
        usuario = conexion.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        conexion.close()

        if usuario is None or not check_password_hash(usuario["password_hash"], password):
            errores.append("Email o contraseña incorrectos.")
        else:
            session["usuario_id"] = usuario["id"]
            session["email"] = usuario["email"]
            return redirect(url_for("panel"))

    return render_template("login.html", errores=errores)


@app.route("/panel")
def panel():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    hoy = date.today()
    mes = hoy.strftime("%Y-%m")

    conexion = conectar()
    filas = conexion.execute(
        "SELECT tipo, SUM(monto) AS total FROM movimientos "
        "WHERE usuario_id = ? AND fecha LIKE ? GROUP BY tipo",
        (session["usuario_id"], mes + "%"),
    ).fetchall()
    conexion.close()

    ingresos = 0
    gastos = 0
    for fila in filas:
        if fila["tipo"] == "ingreso":
            ingresos = fila["total"]
        else:
            gastos = fila["total"]

    saldo = ingresos - gastos
    ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
    dias_restantes = ultimo_dia - hoy.day + 1
    por_dia = saldo / dias_restantes if saldo > 0 else 0

    oficial = obtener_oficial()
    blue = obtener_dolar("blue")

    saldo_usd_oficial = saldo / oficial["venta"] if oficial else None
    saldo_usd_blue = saldo / blue["venta"] if blue else None

    return render_template(
        "panel.html",
        mes=mes,
        ingresos=ingresos,
        gastos=gastos,
        saldo=saldo,
        dias_restantes=dias_restantes,
        por_dia=por_dia,
        oficial=oficial,
        blue=blue,
        saldo_usd_oficial=saldo_usd_oficial,
        saldo_usd_blue=saldo_usd_blue,
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/movimientos")
def movimientos():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    filas = conexion.execute(
        "SELECT * FROM movimientos WHERE usuario_id = ? ORDER BY fecha DESC, id DESC",
        (session["usuario_id"],),
    ).fetchall()
    conexion.close()

    return render_template("movimientos.html", movimientos=filas)


@app.route("/movimientos/nuevo", methods=["GET", "POST"])
def nuevo_movimiento():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    errores = []
    datos = {}

    if request.method == "POST":
        datos = request.form
        tipo = request.form.get("tipo", "")
        descripcion = request.form.get("descripcion", "").strip()
        monto_texto = request.form.get("monto", "").replace(",", ".")
        categoria = request.form.get("categoria", "")
        fecha = request.form.get("fecha", "")

        if tipo not in ("ingreso", "gasto"):
            errores.append("Elegí si es un ingreso o un gasto.")

        if descripcion == "" or len(descripcion) > 60:
            errores.append("La descripción es obligatoria y puede tener hasta 60 caracteres.")

        try:
            monto = float(monto_texto)
            if not math.isfinite(monto) or monto <= 0:
                errores.append("El monto tiene que ser mayor a cero.")
        except ValueError:
            errores.append("El monto tiene que ser un número.")

        if categoria not in CATEGORIAS:
            errores.append("Elegí una categoría de la lista.")

        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            errores.append("La fecha no es válida.")

        if not errores:
            conexion = conectar()
            conexion.execute(
                "INSERT INTO movimientos (usuario_id, tipo, descripcion, monto, categoria, fecha) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session["usuario_id"], tipo, descripcion, monto, categoria, fecha),
            )
            conexion.commit()
            conexion.close()
            flash("Movimiento guardado.")
            return redirect(url_for("movimientos"))

    return render_template(
        "nuevo_movimiento.html",
        errores=errores,
        datos=datos,
        categorias=CATEGORIAS,
        hoy=date.today().isoformat(),
    )


@app.route("/movimientos/<int:id>/eliminar", methods=["POST"])
def eliminar_movimiento(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    conexion.execute(
        "DELETE FROM movimientos WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"]),
    )
    conexion.commit()
    conexion.close()
    flash("Movimiento eliminado.")
    return redirect(url_for("movimientos"))

@app.route("/api/resumen")
def api_resumen():
    if "usuario_id" not in session:
        return jsonify({"error": "Necesitás iniciar sesión"}), 401

    hoy = date.today()
    mes = hoy.strftime("%Y-%m")

    conexion = conectar()
    por_tipo = conexion.execute(
        "SELECT tipo, SUM(monto) AS total FROM movimientos "
        "WHERE usuario_id = ? AND fecha LIKE ? GROUP BY tipo",
        (session["usuario_id"], mes + "%"),
    ).fetchall()
    por_categoria = conexion.execute(
        "SELECT categoria, SUM(monto) AS total FROM movimientos "
        "WHERE usuario_id = ? AND tipo = 'gasto' AND fecha LIKE ? GROUP BY categoria",
        (session["usuario_id"], mes + "%"),
    ).fetchall()
    conexion.close()

    ingresos = 0
    gastos = 0
    for fila in por_tipo:
        if fila["tipo"] == "ingreso":
            ingresos = fila["total"]
        else:
            gastos = fila["total"]

    saldo = ingresos - gastos
    ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
    dias_restantes = ultimo_dia - hoy.day + 1
    por_dia = saldo / dias_restantes if saldo > 0 else 0

    return jsonify({
        "mes": mes,
        "ingresos": ingresos,
        "gastos": gastos,
        "saldo": saldo,
        "dias_restantes": dias_restantes,
        "por_dia": round(por_dia, 2),
        "gastos_por_categoria": {f["categoria"]: f["total"] for f in por_categoria},
    })


@app.route("/api/movimientos")
def api_movimientos():
    if "usuario_id" not in session:
        return jsonify({"error": "Necesitás iniciar sesión"}), 401

    conexion = conectar()
    filas = conexion.execute(
        "SELECT id, tipo, descripcion, monto, categoria, fecha FROM movimientos "
        "WHERE usuario_id = ? ORDER BY fecha DESC, id DESC",
        (session["usuario_id"],),
    ).fetchall()
    conexion.close()

    return jsonify([dict(fila) for fila in filas])


if __name__ == "__main__":
    app.run(debug=True)