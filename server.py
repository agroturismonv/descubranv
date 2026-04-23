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
app.secret_key = os.getenv("SECRET_KEY", "descubranv-dev-secret")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
ADMIN_DIR = os.path.join(BASE_DIR, "admin")
USER_XML_PATH = os.path.join(ADMIN_DIR, "user.xml")
PENDENTES_DIR = os.path.join(BASE_DIR, "pendentes")

site_manager = SiteManager()


def load_users():
    users = {}
    if not os.path.exists(USER_XML_PATH):
        return users

    try:
        root = ET.parse(USER_XML_PATH).getroot()
        for node in root.findall("user"):
            username = (node.findtext("username") or "").strip()
            password = (node.findtext("password") or "").strip()
            level = (node.findtext("level") or "admin").strip()
            if username and password:
                users[username] = {"password": password, "level": level}
    except Exception:
        return {}
    return users


def save_users(users):
    root = ET.Element("users_database")
    for username in sorted(users.keys()):
        user_data = users[username]
        user_el = ET.SubElement(root, "user")
        ET.SubElement(user_el, "username").text = username
        ET.SubElement(user_el, "password").text = user_data.get("password", "")
        ET.SubElement(user_el, "level").text = user_data.get("level", "admin")

    tree = ET.ElementTree(root)
    tree.write(USER_XML_PATH, encoding="utf-8", xml_declaration=True)


def is_logged_in():
    return bool(session.get("admin_user"))


def require_auth():
    if not is_logged_in():
        return jsonify(error="forbidden"), 403
    return None


def parse_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}

    raw = request.form.get("json")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def save_upload_files(payload, files):
    tipo = payload.get("tipo")
    regiao = site_manager.sanitizar(payload.get("regiao"))
    local = site_manager.sanitizar(payload.get("local"))
    cover_file = payload.get("cover_file")
    gallery_names = []

    if tipo == "regiao":
        path_regiao = site_manager.garantir_regiao(regiao)
        images_dir = os.path.join(path_regiao, "images")
        os.makedirs(images_dir, exist_ok=True)

        for uploaded in files:
            name = secure_filename(uploaded.filename or "")
            if not name:
                continue
            uploaded.save(os.path.join(images_dir, name))
        return

    if tipo != "local":
        return

    path_regiao = site_manager.garantir_regiao(regiao)
    path_local = os.path.join(path_regiao, local)
    images_dir = os.path.join(path_local, "images")
    os.makedirs(images_dir, exist_ok=True)

    for uploaded in files:
        name = secure_filename(uploaded.filename or "")
        if not name:
            continue
        uploaded.save(os.path.join(images_dir, name))
        gallery_names.append(name)

    if not payload.get("dados"):
        payload["dados"] = {}

    if not payload["dados"].get("gallery"):
        payload["dados"]["gallery"] = gallery_names

    if not cover_file and gallery_names:
        payload["cover_file"] = gallery_names[0]


def build_listagem_data():
    data = []
    if not os.path.isdir(DADOS_DIR):
        return data

    for regiao_id in sorted(os.listdir(DADOS_DIR)):
        regiao_dir = os.path.join(DADOS_DIR, regiao_id)
        if not os.path.isdir(regiao_dir):
            continue

        config_path = os.path.join(regiao_dir, "config.js")
        config = site_manager.carregar_js_objeto(config_path) or {
            "id": regiao_id,
            "cover": "",
            "texts": {},
            "locais": [],
        }

        textos = config.get("texts", {}).get("pt", {})
        locais = []

        local_ids = list(config.get("locais", []))
        # fallback: if config.js has no locais[] yet, discover by folder names
        if not local_ids:
            for item in sorted(os.listdir(regiao_dir)):
                local_dir = os.path.join(regiao_dir, item)
                local_js = os.path.join(local_dir, f"{item}.js")
                if os.path.isdir(local_dir) and os.path.isfile(local_js):
                    local_ids.append(item)

        for local_id in sorted(set(local_ids)):
            local_dir = os.path.join(regiao_dir, local_id)
            local_js = os.path.join(local_dir, f"{local_id}.js")
            local = site_manager.carregar_js_objeto(local_js) or {
                "id": local_id,
                "hero": "",
                "gallery": [],
                "texts": {},
                "location": {},
                "RAvisionScreen": False,
                "RAvisionlink": "",
            }

            local_texts = local.get("texts", {}).get("pt", {})
            locais.append(
                {
                    "id": local.get("id", local_id),
                    "nome": local_texts.get("title", ""),
                    "subtitulo": local_texts.get("subtitle", ""),
                    "capa": local.get("hero", ""),
                    "fotos": local.get("gallery", []),
                    "texts": local.get("texts", {}),
                    "location": local.get("location", {}),
                    "RAvisionScreen": local.get("RAvisionScreen", False),
                    "RAvisionlink": local.get("RAvisionlink", ""),
                }
            )

        data.append(
            {
                "regiao": config.get("id", regiao_id),
                "titulo": textos.get("title", ""),
                "descricao": textos.get("subtitle", ""),
                "capa": config.get("cover", ""),
                "texts": config.get("texts", {}),
                "locais": locais,
            }
        )

    return data


def get_regiao_or_none(regiao_id):
    regiao_slug = site_manager.sanitizar(regiao_id)
    for regiao in build_listagem_data():
        if site_manager.sanitizar(regiao.get("regiao")) == regiao_slug:
            return regiao
    return None


def get_local_or_none(regiao_id, local_id):
    regiao = get_regiao_or_none(regiao_id)
    if not regiao:
        return None, None

    local_slug = site_manager.sanitizar(local_id)
    for local in regiao.get("locais", []):
        if site_manager.sanitizar(local.get("id")) == local_slug:
            return regiao, local
    return regiao, None


def upsert_from_request(payload):
    files = request.files.getlist("files")
    save_upload_files(payload, files)
    site_manager.criar_ou_atualizar(payload)
    return jsonify(success=True)


def delete_from_payload(payload):
    site_manager.deletar(payload)
    return jsonify(success=True)


@app.route("/")
def root():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/user.xml")
def user_xml():
    return send_from_directory(ADMIN_DIR, "user.xml")


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    user = (body.get("user") or "").strip()
    password = body.get("password") or ""
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    users = load_users()

    if user not in users or users[user]["password"] != password_hash:
        return jsonify(success=False, erro="credenciais inválidas"), 401

    session["admin_user"] = user
    session["admin_level"] = users[user]["level"]
    return jsonify(success=True, user=user, level=users[user]["level"])


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(success=True)


@app.route("/api/check", methods=["GET"])
def check():
    if not is_logged_in():
        return jsonify(logado=False)
    return jsonify(
        logado=True,
        user=session.get("admin_user"),
        level=session.get("admin_level", "admin"),
    )


@app.route("/api/users", methods=["GET"])
def listar_usuarios():
    denied = require_auth()
    if denied:
        return denied

    users = load_users()
    data = [
        {"username": username, "level": user_data.get("level", "admin")}
        for username, user_data in users.items()
    ]
    data.sort(key=lambda item: item["username"].lower())
    return jsonify(success=True, data=data)


@app.route("/api/users", methods=["POST"])
def criar_usuario():
    denied = require_auth()
    if denied:
        return denied

    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    level = (body.get("level") or "admin").strip()

    if not username or not password:
        return jsonify(success=False, erro="username e password são obrigatórios"), 400
    if level not in ("admin", "master"):
        return jsonify(success=False, erro="level inválido"), 400

    users = load_users()
    if username in users:
        return jsonify(success=False, erro="Usuário já existe"), 409

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    users[username] = {"password": password_hash, "level": level}
    save_users(users)
    return jsonify(success=True)


@app.route("/api/users/<username>", methods=["PUT"])
def atualizar_usuario(username):
    denied = require_auth()
    if denied:
        return denied

    users = load_users()
    if username not in users:
        return jsonify(success=False, erro="Usuário não encontrado"), 404

    body = request.get_json(silent=True) or {}
    new_password = body.get("password")
    new_level = body.get("level")

    if new_level is not None and new_level not in ("admin", "master"):
        return jsonify(success=False, erro="level inválido"), 400

    if isinstance(new_password, str) and new_password:
        users[username]["password"] = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
    if isinstance(new_level, str):
        users[username]["level"] = new_level

    save_users(users)
    return jsonify(success=True)


@app.route("/api/users/<username>", methods=["DELETE"])
def excluir_usuario(username):
    denied = require_auth()
    if denied:
        return denied

    current_user = session.get("admin_user")
    if username == current_user:
        return jsonify(success=False, erro="Você não pode remover sua própria conta"), 400

    users = load_users()
    if username not in users:
        return jsonify(success=False, erro="Usuário não encontrado"), 404

    del users[username]
    save_users(users)
    return jsonify(success=True)


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    denied = require_auth()
    if denied:
        return denied

    data = build_listagem_data()
    total_locais = sum(len(reg.get("locais", [])) for reg in data)
    return jsonify(
        {
            "total_locais": total_locais,
            "total_regioes": len(data),
            "status": "ok",
        }
    )


@app.route("/api/listar", methods=["GET"])
def listar():
    denied = require_auth()
    if denied:
        return denied

    return jsonify(success=True, data=build_listagem_data())


@app.route("/api/regioes", methods=["GET"])
def regioes():
    denied = require_auth()
    if denied:
        return denied
    return jsonify(success=True, data=build_listagem_data())


@app.route("/api/regioes/<regiao_id>", methods=["GET"])
def regiao_por_id(regiao_id):
    denied = require_auth()
    if denied:
        return denied

    regiao = get_regiao_or_none(regiao_id)
    if not regiao:
        return jsonify(success=False, erro="Região não encontrada"), 404
    return jsonify(success=True, data=regiao)


@app.route("/api/regioes", methods=["POST"])
def criar_regiao():
    denied = require_auth()
    if denied:
        return denied

    payload = parse_payload()
    if not payload:
        return jsonify(success=False, erro="JSON não enviado"), 400

    payload["tipo"] = "regiao"
    if not payload.get("regiao"):
        return jsonify(success=False, erro="regiao é obrigatório"), 400

    try:
        return upsert_from_request(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/regioes/<regiao_id>", methods=["PUT"])
def atualizar_regiao(regiao_id):
    denied = require_auth()
    if denied:
        return denied

    if not get_regiao_or_none(regiao_id):
        return jsonify(success=False, erro="Região não encontrada"), 404

    payload = parse_payload()
    payload["tipo"] = "regiao"
    payload["regiao"] = regiao_id

    try:
        return upsert_from_request(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/regioes/<regiao_id>", methods=["DELETE"])
def excluir_regiao(regiao_id):
    denied = require_auth()
    if denied:
        return denied

    if not get_regiao_or_none(regiao_id):
        return jsonify(success=False, erro="Região não encontrada"), 404

    payload = {"tipo": "regiao", "regiao": regiao_id}
    try:
        return delete_from_payload(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/locais", methods=["GET"])
def locais():
    denied = require_auth()
    if denied:
        return denied

    data = build_listagem_data()
    flattened = []
    for reg in data:
        for local in reg.get("locais", []):
            item = dict(local)
            item["regiao"] = reg.get("regiao")
            item["regiao_nome"] = reg.get("titulo")
            flattened.append(item)
    return jsonify(success=True, data=flattened)


@app.route("/api/regioes/<regiao_id>/locais", methods=["GET"])
def locais_por_regiao(regiao_id):
    denied = require_auth()
    if denied:
        return denied

    regiao = get_regiao_or_none(regiao_id)
    if not regiao:
        return jsonify(success=False, erro="Região não encontrada"), 404
    return jsonify(success=True, data=regiao.get("locais", []))


@app.route("/api/regioes/<regiao_id>/locais/<local_id>", methods=["GET"])
def local_por_id(regiao_id, local_id):
    denied = require_auth()
    if denied:
        return denied

    regiao, local = get_local_or_none(regiao_id, local_id)
    if not regiao:
        return jsonify(success=False, erro="Região não encontrada"), 404
    if not local:
        return jsonify(success=False, erro="Local não encontrado"), 404
    return jsonify(success=True, data=local)


@app.route("/api/regioes/<regiao_id>/locais", methods=["POST"])
def criar_local(regiao_id):
    denied = require_auth()
    if denied:
        return denied

    if not get_regiao_or_none(regiao_id):
        return jsonify(success=False, erro="Região não encontrada"), 404

    payload = parse_payload()
    payload["tipo"] = "local"
    payload["regiao"] = regiao_id
    if not payload.get("local"):
        return jsonify(success=False, erro="local é obrigatório"), 400

    try:
        return upsert_from_request(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/regioes/<regiao_id>/locais/<local_id>", methods=["PUT"])
def atualizar_local(regiao_id, local_id):
    denied = require_auth()
    if denied:
        return denied

    regiao, local = get_local_or_none(regiao_id, local_id)
    if not regiao:
        return jsonify(success=False, erro="Região não encontrada"), 404
    if not local:
        return jsonify(success=False, erro="Local não encontrado"), 404

    payload = parse_payload()
    payload["tipo"] = "local"
    payload["regiao"] = regiao_id
    payload["local"] = local_id

    try:
        return upsert_from_request(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/regioes/<regiao_id>/locais/<local_id>", methods=["DELETE"])
def excluir_local(regiao_id, local_id):
    denied = require_auth()
    if denied:
        return denied

    regiao, local = get_local_or_none(regiao_id, local_id)
    if not regiao:
        return jsonify(success=False, erro="Região não encontrada"), 404
    if not local:
        return jsonify(success=False, erro="Local não encontrado"), 404

    payload = {"tipo": "local", "regiao": regiao_id, "local": local_id}
    try:
        return delete_from_payload(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/cadastro", methods=["POST"])
def cadastro():
    denied = require_auth()
    if denied:
        return denied

    payload = parse_payload()
    if not payload:
        return jsonify(success=False, erro="JSON não enviado"), 400

    try:
        return upsert_from_request(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/delete", methods=["POST"])
def delete():
    denied = require_auth()
    if denied:
        return denied

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify(success=False, erro="payload inválido"), 400

    try:
        return delete_from_payload(payload)
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500


@app.route("/api/rebuild", methods=["POST"])
def rebuild():
    denied = require_auth()
    if denied:
        return denied

    try:
        build()
        return jsonify(success=True, message="Rebuild executado com sucesso")
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500


@app.route("/api/upload_zip", methods=["POST"])
def upload_zip():
    denied = require_auth()
    if denied:
        return denied

    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify(success=False, erro="Arquivo ZIP não enviado"), 400

    filename = secure_filename(uploaded.filename or "upload.zip")
    if not filename.lower().endswith(".zip"):
        return jsonify(success=False, erro="Arquivo precisa ser .zip"), 400

    os.makedirs(PENDENTES_DIR, exist_ok=True)

    temp_path = os.path.join(PENDENTES_DIR, filename)
    uploaded.save(temp_path)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(temp_path, "r") as archive:
                archive.extractall(temp_dir)

            circuitos_dir = os.path.join(temp_dir, "dados", "circuitos")
            if os.path.isdir(circuitos_dir):
                for item in os.listdir(circuitos_dir):
                    src = os.path.join(circuitos_dir, item)
                    dst = os.path.join(DADOS_DIR, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
            else:
                for item in os.listdir(temp_dir):
                    src = os.path.join(temp_dir, item)
                    dst = os.path.join(DADOS_DIR, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)

        build()
        return jsonify(success=True, message="ZIP importado com sucesso")
    except Exception as exc:
        return jsonify(success=False, erro=str(exc)), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route("/download_zip/<regiao>/<local>", methods=["GET"])
def download_zip(regiao, local):
    denied = require_auth()
    if denied:
        return denied

    regiao_slug = site_manager.sanitizar(regiao)
    local_slug = site_manager.sanitizar(local)
    source_dir = os.path.join(DADOS_DIR, regiao_slug, local_slug)

    if not os.path.isdir(source_dir):
        return jsonify(success=False, erro="Local não encontrado"), 404

    temp_dir = tempfile.mkdtemp()
    archive_name = f"{local_slug}.zip"
    archive_base = os.path.join(temp_dir, local_slug)
    shutil.make_archive(archive_base, "zip", source_dir)
    return send_from_directory(temp_dir, archive_name, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
