# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Configuración Híbrida Inteligente (Local / Nube)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

if os.environ.get("RENDER"):
    DATA_DIR = "/opt/render/project/src/data"
else:
    DATA_DIR = BASE_DIR

UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "database"), exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "clave_secreta_lira_investigacion_2026"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(DATA_DIR, 'database', 'datasheets.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# CONTRASEÑA MAESTRA DEL CREADOR (Cambia 'lira2026' por la clave que tú quieras)
CLAVE_MAESTRA = "lira2026"

# Modelo de datos para SQLite
class Datasheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    component_name = db.Column(db.String(120), nullable=False)
    part_number = db.Column(db.String(80), nullable=False)
    filename = db.Column(db.String(260), nullable=False)  
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Rutas del servidor
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        component_name = request.form.get("component_name", "").strip()
        part_number = request.form.get("part_number", "").strip()
        file = request.files.get("pdf_file")
        password_input = request.form.get("admin_password", "").strip()

        # 🔐 CANDADO DE SEGURIDAD EXCLUSIVO PARA EL CREADOR
        if password_input != CLAVE_MAESTRA:
            flash("❌ Acceso Denegado: Contraseña incorrecta. Solo el administrador puede subir archivos.", "danger")
            return redirect(url_for("index"))

        if not component_name or not part_number:
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("index"))

        if not file or file.filename == "":
            flash("Debe seleccionar un archivo PDF.", "danger")
            return redirect(url_for("index"))

        if not allowed_file(file.filename):
            flash("Solo se permiten archivos PDF.", "danger")
            return redirect(url_for("index"))

        # Guardado seguro del archivo físico con timestamp único
        original_filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        stored_filename = f"{timestamp}_{original_filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)
        file.save(file_path)

        # Registro o actualización en la base de datos
        new_entry = Datasheet(
            component_name=component_name,
            part_number=part_number,
            filename=stored_filename,
        )
        db.session.add(new_entry)
        db.session.commit()

        flash("¡Datasheet subido al almacén con éxito, Creador!", "success")
        return redirect(url_for("index"))

    datasheets = Datasheet.query.order_by(Datasheet.upload_date.desc()).all()
    return render_template("index.html", datasheets=datasheets)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Crear las tablas de la base de datos de forma segura al arrancar
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
