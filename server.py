from flask import Flask, jsonify, request, send_from_directory, session
import hashlib
import json
import os
import tempfile
import shutil
import zipfile
import xml.etree.ElementTree as ET
from werkzeug.utils import secure_filename

from manager import SiteManager
from generator import build


# -------------------------
# CONFIG
# -------------------------
app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
ADMIN_DIR = os.path.join(BASE_DIR, "admin")
USER_XML = os.path.join(ADMIN_DIR, "user.xml")
PENDENTES = os.path.join(BASE_DIR, "pendentes")

site = SiteManager()


# -------------------------
# AUTH
# -------------------------
def load_users():
    users = {}
    if not os.path.exists(USER_XML):
        return users

    root = ET.parse(USER_XML).getroot()
    for u in root.findall("user"):
        username = u.findtext("username")
        password = u.findtext("password")
        level = u.findtext("level") or "admin"

        if username and password:
            users[username] = {"password": password, "level": level}

    return users


def save_users(users):
    root = ET.Element("users_database")

    for username, data in users.items():
        u = ET.SubElement(root, "user")
        ET.SubElement(u, "username").text = username
        ET.SubElement(u, "password").text = data["password"]
        ET.SubElement(u, "level").text = data["level"]

    ET.ElementTree(root).write(USER_XML, encoding="utf-8", xml_declaration=True)


def auth_required():
    if not session.get("user"):
        return jsonify(error="unauthorized"), 403
    return None


# -------------------------
# HELPERS
# -------------------------
def parse_payload():
    if request.is_json:
        return request.get_json()
    raw = request.form.get("json")
    return json.loads(raw) if raw else {}


def auto_rebuild():
    """Sempre mantém sistema consistente"""
    try:
        build()
    except Exception as e:
        print("[ERRO BUILD]", e)


# -------------------------
# LOGIN
# -------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user = data.get("user")
    password = data.get("password")

    users = load_users()
    hashed = hashlib.sha256(password.encode()).hexdigest()

    if user not in users or users[user]["password"] != hashed:
        return jsonify(success=False), 401

    session["user"] = user
    session["level"] = users[user]["level"]

    return jsonify(success=True)


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(success=True)


@app.route("/api/check")
def check():
    return jsonify(
        logado=bool(session.get("user")),
        user=session.get("user"),
        level=session.get("level"),
    )


# -------------------------
# DASHBOARD
# -------------------------
@app.route("/api/dashboard")
def dashboard():
    denied = auth_required()
    if denied:
        return denied

    data = site.listar()

    total_locais = sum(len(r["locais"]) for r in data)

    return jsonify({
        "total_regioes": len(data),
        "total_locais": total_locais,
        "status": "ok"
    })


# -------------------------
# LISTAGEM
# -------------------------
@app.route("/api/listar")
def listar():
    denied = auth_required()
    if denied:
        return denied

    try:
        data = site.listar()
        return jsonify(success=True, data=data)
    except Exception as e:
        print("[ERRO LISTAR]", e)
        return jsonify(success=False, erro=str(e)), 500


# -------------------------
# REGIÕES
# -------------------------
@app.route("/api/regioes", methods=["POST"])
def criar_regiao():
    denied = auth_required()
    if denied:
        return denied

    payload = parse_payload()
    payload["tipo"] = "regiao"

    site.salvar(payload)
    auto_rebuild()

    return jsonify(success=True)


@app.route("/api/regioes/<regiao>", methods=["DELETE"])
def deletar_regiao(regiao):
    denied = auth_required()
    if denied:
        return denied

    site.deletar({"tipo": "regiao", "regiao": regiao})
    auto_rebuild()

    return jsonify(success=True)


# -------------------------
# LOCAIS
# -------------------------
@app.route("/api/locais", methods=["POST"])
def criar_local():
    denied = auth_required()
    if denied:
        return denied

    payload = parse_payload()
    payload["tipo"] = "local"

    site.salvar(payload)
    auto_rebuild()

    return jsonify(success=True)


@app.route("/api/locais", methods=["DELETE"])
def deletar_local():
    denied = auth_required()
    if denied:
        return denied

    payload = request.get_json()

    site.deletar(payload)
    auto_rebuild()

    return jsonify(success=True)


# -------------------------
# UPLOAD ZIP
# -------------------------
@app.route("/api/upload_zip", methods=["POST"])
def upload_zip():
    denied = auth_required()
    if denied:
        return denied

    file = request.files.get("file")
    if not file:
        return jsonify(success=False, erro="sem arquivo")

    os.makedirs(PENDENTES, exist_ok=True)

    temp_zip = os.path.join(PENDENTES, secure_filename(file.filename))
    file.save(temp_zip)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(temp_zip) as z:
                z.extractall(tmp)

            for item in os.listdir(tmp):
                src = os.path.join(tmp, item)
                dst = os.path.join(DADOS_DIR, item)

                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)

        auto_rebuild()
        return jsonify(success=True)

    except Exception as e:
        return jsonify(success=False, erro=str(e))

    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)


# -------------------------
# DOWNLOAD ZIP
# -------------------------
@app.route("/download/<regiao>/<local>")
def download(regiao, local):
    denied = auth_required()
    if denied:
        return denied

    path = os.path.join(DADOS_DIR, regiao, local)

    if not os.path.isdir(path):
        return jsonify(error="não encontrado"), 404

    temp = tempfile.mkdtemp()
    zip_path = os.path.join(temp, local)

    shutil.make_archive(zip_path, "zip", path)

    return send_from_directory(temp, f"{local}.zip", as_attachment=True)


# -------------------------
# STATIC
# -------------------------
@app.route("/")
def root():
    return send_from_directory(BASE_DIR, "index.html")


# -------------------------
# START
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
