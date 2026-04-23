from flask import Flask, jsonify, request, send_from_directory, session
import hashlib
import json
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from werkzeug.utils import secure_filename

from generator import build
from manager import SiteManager

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
ADMIN_DIR = os.path.join(BASE_DIR, "admin")
USER_XML_PATH = os.path.join(ADMIN_DIR, "user.xml")
PENDENTES_DIR = os.path.join(BASE_DIR, "pendentes")

site_manager = SiteManager()

# =========================
# AUTH
# =========================
def load_users():
    if not os.path.exists(USER_XML_PATH):
        return {}

    try:
        root = ET.parse(USER_XML_PATH).getroot()
        return {
            node.findtext("username"): {
                "password": node.findtext("password"),
                "level": node.findtext("level") or "admin"
            }
            for node in root.findall("user")
        }
    except:
        return {}


def is_logged_in():
    return bool(session.get("admin_user"))


def require_auth():
    if not is_logged_in():
        return jsonify(success=False, error="forbidden"), 403
    return None


# =========================
# UTIL
# =========================
def parse_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}

    raw = request.form.get("json")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except:
        return {}


def safe_build():
    try:
        build()
    except Exception as e:
        print("[BUILD ERROR]", e)


# =========================
# FILE UPLOAD
# =========================
def save_upload_files(payload):
    files = request.files.getlist("files")

    tipo = payload.get("tipo")
    regiao = site_manager.sanitizar(payload.get("regiao"))
    local = site_manager.sanitizar(payload.get("local"))

    if tipo == "regiao":
        path = site_manager.garantir_regiao(regiao)
        images_dir = os.path.join(path, "images")
        os.makedirs(images_dir, exist_ok=True)

        for f in files:
            name = secure_filename(f.filename or "")
            if name:
                f.save(os.path.join(images_dir, name))
        return

    if tipo != "local":
        return

    path = os.path.join(site_manager.garantir_regiao(regiao), local)
    images_dir = os.path.join(path, "images")
    os.makedirs(images_dir, exist_ok=True)

    gallery = []

    for f in files:
        name = secure_filename(f.filename or "")
        if name:
            f.save(os.path.join(images_dir, name))
            gallery.append(name)

    payload.setdefault("dados", {})
    payload["dados"].setdefault("gallery", gallery)

    if not payload.get("cover_file") and gallery:
        payload["cover_file"] = gallery[0]


# =========================
# CORE ACTIONS
# =========================
def upsert(payload):
    save_upload_files(payload)
    site_manager.criar_ou_atualizar(payload)
    safe_build()
    return jsonify(success=True)


def delete(payload):
    site_manager.deletar(payload)
    safe_build()
    return jsonify(success=True)


# =========================
# DATA READ (ROBUSTO)
# =========================
def build_listagem_data():
    data = []

    if not os.path.isdir(DADOS_DIR):
        return data

    for regiao_id in sorted(os.listdir(DADOS_DIR)):
        regiao_dir = os.path.join(DADOS_DIR, regiao_id)

        if not os.path.isdir(regiao_dir):
            continue

        config = site_manager.carregar_js_objeto(
            os.path.join(regiao_dir, "config.js")
        )

        if not config:
            print(f"[SKIP] config inválido: {regiao_id}")
            continue

        textos = config.get("texts", {}).get("pt", {})

        locais = []

        for local_id in config.get("locais", []):
            local_path = os.path.join(regiao_dir, local_id)
            local_js = os.path.join(local_path, f"{local_id}.js")

            if not os.path.isfile(local_js):
                continue

            local = site_manager.carregar_js_objeto(local_js)
            if not local:
                continue

            t = local.get("texts", {}).get("pt", {})

            locais.append({
                "id": local.get("id"),
                "nome": t.get("title", ""),
                "subtitulo": t.get("subtitle", ""),
                "capa": local.get("hero", ""),
                "fotos": local.get("gallery", []),
                "texts": local.get("texts", {}),
            })

        data.append({
            "regiao": config.get("id"),
            "titulo": textos.get("title", ""),
            "descricao": textos.get("subtitle", ""),
            "capa": config.get("cover", ""),
            "locais": locais,
        })

    return data


# =========================
# ROUTES
# =========================
@app.route("/")
def root():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json() or {}

    user = body.get("user")
    password = body.get("password")

    users = load_users()

    if user not in users:
        return jsonify(success=False), 401

    hash_pass = hashlib.sha256(password.encode()).hexdigest()

    if users[user]["password"] != hash_pass:
        return jsonify(success=False), 401

    session["admin_user"] = user
    return jsonify(success=True)


@app.route("/api/listar")
def listar():
    denied = require_auth()
    if denied:
        return denied

    return jsonify(success=True, data=build_listagem_data())


@app.route("/api/cadastro", methods=["POST"])
def cadastro():
    denied = require_auth()
    if denied:
        return denied

    payload = parse_payload()
    return upsert(payload)


@app.route("/api/delete", methods=["POST"])
def delete_route():
    denied = require_auth()
    if denied:
        return denied

    payload = request.get_json()
    return delete(payload)


@app.route("/api/rebuild", methods=["POST"])
def rebuild():
    denied = require_auth()
    if denied:
        return denied

    safe_build()
    return jsonify(success=True)


# =========================
# ZIP
# =========================
@app.route("/api/upload_zip", methods=["POST"])
def upload_zip():
    denied = require_auth()
    if denied:
        return denied

    file = request.files.get("file")

    if not file or not file.filename.endswith(".zip"):
        return jsonify(success=False, erro="ZIP inválido"), 400

    os.makedirs(PENDENTES_DIR, exist_ok=True)

    path = os.path.join(PENDENTES_DIR, secure_filename(file.filename))
    file.save(path)

    try:
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(path) as z:
                z.extractall(temp)

            for item in os.listdir(temp):
                src = os.path.join(temp, item)
                dst = os.path.join(DADOS_DIR, item)

                if not os.path.isdir(src):
                    continue

                # 🔥 valida antes de copiar
                if not os.path.isfile(os.path.join(src, "config.js")):
                    print("[SKIP ZIP]", item)
                    continue

                if os.path.exists(dst):
                    shutil.rmtree(dst)

                shutil.copytree(src, dst)

        safe_build()
        return jsonify(success=True)

    except Exception as e:
        return jsonify(success=False, erro=str(e)), 500


@app.route("/download_zip/<regiao>/<local>")
def download_zip(regiao, local):
    denied = require_auth()
    if denied:
        return denied

    regiao = site_manager.sanitizar(regiao)
    local = site_manager.sanitizar(local)

    src = os.path.join(DADOS_DIR, regiao, local)

    if not os.path.isdir(src):
        return jsonify(success=False), 404

    temp = tempfile.mkdtemp()
    zip_path = os.path.join(temp, local)

    shutil.make_archive(zip_path, "zip", src)

    return send_from_directory(temp, f"{local}.zip", as_attachment=True)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
