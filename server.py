from flask import Flask, jsonify, request, send_from_directory, session
import hashlib, json, os, re, tempfile, shutil, zipfile
import xml.etree.ElementTree as ET
from werkzeug.utils import secure_filename
from git_sync import sync_async as _git_sync
from manager import SiteManager
from generator import build

# ── CONFIG ────────────────────────────────────────────────
app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
ADMIN_DIR = os.path.join(BASE_DIR, "admin")
USER_XML  = os.path.join(ADMIN_DIR, "user.xml")
PENDENTES = os.path.join(BASE_DIR, "pendentes")

site = SiteManager()

def _sanitize(v):
    return re.sub(r'[^a-z0-9_]', '', (v or "").lower().replace(" ", "_"))

# ── USERS ─────────────────────────────────────────────────
def load_users():
    if not os.path.exists(USER_XML):
        return {}
    root = ET.parse(USER_XML).getroot()
    return {
        u.findtext("username"): {
            "password": u.findtext("password"),
            "level": u.findtext("level") or "admin"
        }
        for u in root.findall("user")
        if u.findtext("username") and u.findtext("password")
    }

def save_users(users):
    root = ET.Element("users_database")
    for username, data in users.items():
        u = ET.SubElement(root, "user")
        ET.SubElement(u, "username").text = username
        ET.SubElement(u, "password").text = data["password"]
        ET.SubElement(u, "level").text = data["level"]
    ET.ElementTree(root).write(USER_XML, encoding="utf-8", xml_declaration=True)

# ── AUTH HELPERS ──────────────────────────────────────────
def auth_required():
    if not session.get("user"):
        return jsonify(error="unauthorized"), 403
    return None

def parse_payload():
    if request.is_json:
        return request.get_json() or {}
    raw = request.form.get("json")
    return json.loads(raw) if raw else {}

def auto_rebuild(git_msg: str = "chore: update dados"):
    try:
        build()
    except Exception as e:
        print("[ERRO BUILD]", e)
    if os.getenv("GIT_TOKEN"):
        _git_sync(git_msg)

# ── FILE UPLOAD HELPER ────────────────────────────────────
def save_uploaded_files(files, dest_dir):
    """
    Salva lista de FileStorage em dest_dir/images/.
    Retorna dict {filename: path_relativo_à_BASE_DIR}.
    """
    if not files:
        return {}
    images_dir = os.path.join(dest_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    result = {}
    for f in files:
        fname = secure_filename(f.filename)
        if not fname:
            continue
        full_path = os.path.join(images_dir, fname)
        f.save(full_path)
        rel = os.path.relpath(full_path, BASE_DIR).replace(os.sep, "/")
        result[fname] = rel
    return result

def enrich_payload_with_files(payload):
    """
    Salva os arquivos do request.files e atualiza cover_file e gallery
    no payload com os paths relativos corretos.
    Retorna o payload enriquecido.
    """
    files = request.files.getlist("files")
    if not files or not any(f.filename for f in files):
        return payload

    tipo   = payload.get("tipo", "")
    regiao = _sanitize(payload.get("regiao", ""))
    local  = _sanitize(payload.get("local", ""))

    if tipo == "regiao" and regiao:
        dest = os.path.join(DADOS_DIR, regiao)
    elif tipo == "local" and regiao and local:
        dest = os.path.join(DADOS_DIR, regiao, local)
    else:
        return payload

    saved = save_uploaded_files(files, dest)
    if not saved:
        return payload

    # Atualiza cover_file se for um nome de arquivo simples
    cover = payload.get("cover_file", "") or ""
    basename = os.path.basename(cover)
    if basename in saved:
        payload["cover_file"] = saved[basename]

    # Atualiza gallery: substitui filenames por paths relativos
    dados = payload.get("dados", {})
    gallery = dados.get("gallery", [])
    if gallery:
        dados["gallery"] = [
            saved.get(os.path.basename(g), g) for g in gallery
        ]
        payload["dados"] = dados

    return payload

# ── LOGIN ─────────────────────────────────────────────────
@app.route("/admin")
def admin_login():
    return send_from_directory(ADMIN_DIR, "login.html")

@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    user     = data.get("user", "")
    password = data.get("password", "")
    users    = load_users()
    hashed   = hashlib.sha256(password.encode()).hexdigest()
    if user not in users or users[user]["password"] != hashed:
        return jsonify(success=False), 401
    session["user"]  = user
    session["level"] = users[user]["level"]
    # CORRIGIDO: retorna o username para o JS armazenar no sessionStorage
    return jsonify(success=True, user=user, level=users[user]["level"])

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

# ── DASHBOARD ────────────────────────────────────────────
@app.route("/api/dashboard")
def dashboard():
    denied = auth_required()
    if denied: return denied
    data = site.listar()
    return jsonify({
        "total_regioes": len(data),
        "total_locais":  sum(len(r["locais"]) for r in data),
        "status": "ok"
    })

@app.route("/api/rebuild", methods=["POST"])
def rebuild():
    denied = auth_required()
    if denied: return denied
    try:
        build()
        return jsonify(success=True, message="Rebuild concluído com sucesso.")
    except Exception as e:
        return jsonify(success=False, erro=str(e)), 500

# ── ROTA DO AR - Léo ──────────────────────────────────────────────
@app.route("/totem")
def ra():
    return redirect("https://mobogames.com.br/descubranv")

# ── LISTAGEM ──────────────────────────────────────────────
@app.route("/api/listar")
def listar():
    denied = auth_required()
    if denied: return denied
    try:
        return jsonify(success=True, data=site.listar())
    except Exception as e:
        return jsonify(success=False, erro=str(e)), 500

# ── REGIÕES ───────────────────────────────────────────────
@app.route("/api/regioes", methods=["GET"])
def listar_regioes():
    denied = auth_required()
    if denied: return denied
    return jsonify(success=True, data=site.listar())

@app.route("/api/regioes", methods=["POST"])
def criar_regiao():
    denied = auth_required()
    if denied: return denied
    payload = enrich_payload_with_files(parse_payload())
    payload["tipo"] = "regiao"
    site.criar_ou_atualizar(payload)
    auto_rebuild(f"feat: adicionar região '{payload.get('regiao', '')}'")
    return jsonify(success=True)

@app.route("/api/regioes/<regiao>", methods=["GET"])
def get_regiao(regiao):
    denied = auth_required()
    if denied: return denied
    for r in site.listar():
        if r["regiao"] == regiao:
            return jsonify(success=True, data=r)
    return jsonify(success=False, erro="não encontrada"), 404

@app.route("/api/regioes/<regiao>", methods=["PUT"])
def atualizar_regiao(regiao):
    denied = auth_required()
    if denied: return denied
    payload = enrich_payload_with_files(parse_payload())
    payload.update({"tipo": "regiao", "regiao": regiao})
    site.criar_ou_atualizar(payload)
    auto_rebuild(f"fix: atualizar região '{regiao}'")
    return jsonify(success=True)

@app.route("/api/regioes/<regiao>", methods=["DELETE"])
def deletar_regiao(regiao):
    denied = auth_required()
    if denied: return denied
    site.deletar({"tipo": "regiao", "regiao": regiao})
    auto_rebuild(f"remove: deletar região '{regiao}'")
    return jsonify(success=True)

@app.route('/dados/<path:filename>')
def serve_dados(filename):
    return send_from_directory(os.path.join(BASE_DIR, "dados"), filename)
# ── LOCAIS ────────────────────────────────────────────────
@app.route("/api/regioes/<regiao>/locais/<local>", methods=["GET"])
def get_local(regiao, local):
    denied = auth_required()
    if denied: return denied
    for r in site.listar():
        if r["regiao"] == regiao:
            for loc in r["locais"]:
                if loc["id"] == local:
                    return jsonify(success=True, data=loc)
    return jsonify(success=False, erro="não encontrado"), 404

@app.route("/api/regioes/<regiao>/locais/<local>", methods=["PUT"])
def atualizar_local(regiao, local):
    denied = auth_required()
    if denied: return denied
    payload = enrich_payload_with_files(parse_payload())
    payload.update({"tipo": "local", "regiao": regiao, "local": local})
    site.criar_ou_atualizar(payload)
    auto_rebuild(f"fix: atualizar local '{local}' em '{regiao}'")
    return jsonify(success=True)

@app.route("/api/locais", methods=["POST"])
def criar_local():
    denied = auth_required()
    if denied: return denied
    payload = enrich_payload_with_files(parse_payload())
    payload["tipo"] = "local"
    site.criar_ou_atualizar(payload)
    auto_rebuild(f"feat: adicionar local '{payload.get('local', '')}' em '{payload.get('regiao', '')}'")
    return jsonify(success=True)

@app.route("/api/locais", methods=["DELETE"])
def deletar_local():
    denied = auth_required()
    if denied: return denied
    site.deletar(request.get_json() or {})
    auto_rebuild("remove: deletar local")
    return jsonify(success=True)

# ── CADASTRO UNIFICADO ────────────────────────────────────
@app.route("/api/cadastro", methods=["POST"])
def cadastro():
    """Rota usada por cadastro_online.html para criar região ou local."""
    denied = auth_required()
    if denied: return denied
    payload = enrich_payload_with_files(parse_payload())
    if not payload.get("tipo"):
        return jsonify(success=False, erro="campo tipo obrigatório"), 400
    try:
        site.criar_ou_atualizar(payload)
        tipo = payload.get("tipo", "")
        nome = payload.get("local") or payload.get("regiao") or "item"
        auto_rebuild(f"feat: cadastro de {tipo} '{nome}'")
        return jsonify(success=True)
    except Exception as e:
        print("[ERRO CADASTRO]", e)
        return jsonify(success=False, erro=str(e)), 500

# ── DELETE UNIFICADO ──────────────────────────────────────
@app.route("/api/delete", methods=["POST"])
def delete_unificado():
    """Rota usada por API.delete() em auth.js."""
    denied = auth_required()
    if denied: return denied
    payload = request.get_json() or {}
    if payload.get("tipo") not in ("regiao", "local"):
        return jsonify(success=False, erro="tipo inválido"), 400
    try:
        site.deletar(payload)
        tipo = payload.get("tipo", "item")
        nome = payload.get("local") or payload.get("regiao") or ""
        auto_rebuild(f"remove: deletar {tipo} '{nome}'")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, erro=str(e)), 500

# ── USUÁRIOS ──────────────────────────────────────────────
@app.route("/api/users", methods=["GET"])
def listar_users():
    denied = auth_required()
    if denied: return denied
    if session.get("level") != "master":
        return jsonify(error="forbidden"), 403
    users = load_users()
    return jsonify(success=True, data=[
        {"username": u, "level": d["level"]} for u, d in users.items()
    ])

@app.route("/api/users", methods=["POST"])
def criar_user():
    denied = auth_required()
    if denied: return denied
    if session.get("level") != "master":
        return jsonify(error="forbidden"), 403
    payload  = request.get_json() or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    level    = payload.get("level", "admin")
    if not username or not password:
        return jsonify(success=False, erro="username e password obrigatórios"), 400
    users = load_users()
    if username in users:
        return jsonify(success=False, erro="usuário já existe"), 409
    users[username] = {
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "level": level
    }
    save_users(users)
    return jsonify(success=True)

@app.route("/api/users/<username>", methods=["DELETE"])
def deletar_user(username):
    denied = auth_required()
    if denied: return denied
    if session.get("level") != "master":
        return jsonify(error="forbidden"), 403
    if username == session.get("user"):
        return jsonify(success=False, erro="não pode remover o próprio usuário"), 400
    users = load_users()
    if username not in users:
        return jsonify(success=False, erro="usuário não encontrado"), 404
    del users[username]
    save_users(users)
    return jsonify(success=True)

# ── UPLOAD ZIP ────────────────────────────────────────────
@app.route("/api/upload_zip", methods=["POST"])
def upload_zip():
    denied = auth_required()
    if denied: return denied
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
        auto_rebuild("feat: importar dados via ZIP")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, erro=str(e))
    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)

# ── DOWNLOAD ZIP ──────────────────────────────────────────
@app.route("/download/<regiao>/<local>")
def download(regiao, local):
    denied = auth_required()
    if denied: return denied
    path = os.path.join(DADOS_DIR, regiao, local)
    if not os.path.isdir(path):
        return jsonify(error="não encontrado"), 404
    temp = tempfile.mkdtemp()
    zip_path = os.path.join(temp, local)
    shutil.make_archive(zip_path, "zip", path)
    return send_from_directory(temp, f"{local}.zip", as_attachment=True)

# ── STATIC ────────────────────────────────────────────────
@app.route("/")
def root():
    return send_from_directory(BASE_DIR, "index.html")

# ── START ─────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
