from flask import Flask, jsonify, render_template, request, session

from routes.citas_routes import citas_bp
from routes.laboratorio_routes import laboratorio_bp
from routes.medicos_routes import medicos_bp
from routes.pacientes_routes import pacientes_bp


app = Flask(__name__)
app.secret_key = "hospital-dev-secret"

app.register_blueprint(pacientes_bp, url_prefix="/api/pacientes")
app.register_blueprint(citas_bp, url_prefix="/api/citas")
app.register_blueprint(medicos_bp, url_prefix="/api/medicos")
app.register_blueprint(laboratorio_bp, url_prefix="/api")


@app.route("/")
def lobby():
    return render_template("recepcion.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/dashboard_recepcion")
def dashboard_recepcion():
    return render_template("dashboard_recepcion.html")


@app.route("/dashboard_laboratorio")
def dashboard_laboratorio():
    return render_template("dashboard_laboratorio.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    datos = request.get_json(silent=True) or {}

    correo = datos.get("correo")
    contrasena = datos.get("contrasena")
    rol = datos.get("rol")

    usuarios_credenciales = {
        "recepcion@ipn.mx": {
            "contrasena": "hospital123",
            "rol": "recepcionista",
            "redirect": "/dashboard_recepcion",
        },
        "lab@ipn.mx": {
            "contrasena": "calidad123",
            "rol": "laboratorista",
            "redirect": "/dashboard_laboratorio",
        },
    }

    usuario_valido = usuarios_credenciales.get(correo)

    if usuario_valido and usuario_valido["contrasena"] == contrasena and usuario_valido["rol"] == rol:
        session["correo"] = correo
        session["rol"] = rol
        return jsonify({"mensaje": "Inicio de sesion correcto", "rol": rol, "redirect_url": usuario_valido["redirect"]}), 200

    return jsonify({"error": "Credenciales invalidas o rol incorrecto para este usuario."}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"mensaje": "Sesion cerrada"}), 200


if __name__ == "__main__":
    app.run(debug=True)
