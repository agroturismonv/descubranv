from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
import os
from manager import SiteManager

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = "super-secret-key"

manager = SiteManager()

# =========================
# AUTH DECORATOR
# =========================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logado"):
            return jsonify({"success": False, "erro": "não autorizado"}), 403
        return f(*args, **kwargs)
    return decorated

# =========================
# FRONTEND
# =========================
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/admin/<path:path>")
def admin(path):
    return send_from_directory("admin", path)

# =========================
# AUTH API
# =========================
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json

    user = data.get("user")
    password = data.get("password")

    if user == "admin" and password == "123":
        session["logado"] = True
        return jsonify({"success": True})

    return jsonify({"success": False}), 403


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/check", methods=["GET"])
def api_check():
    return jsonify({"logado": bool(session.get("logado"))})

# =========================
# API PROTEGIDA
# =========================
@app.route('/api/listar', methods=['GET'])
@login_required
def listar():
    try:
        base = os.path.join("dados", "circuitos")
        resultado = []

        if not os.path.exists(base):
            return jsonify({"success": True, "data": []})

        import re

        for regiao in sorted(os.listdir(base)):
            path_regiao = os.path.join(base, regiao)

            if not os.path.isdir(path_regiao):
                continue

            config_path = os.path.join(path_regiao, "config.js")
            if not os.path.exists(config_path):
                continue

            with open(config_path, "r", encoding="utf-8") as f:
                config_raw = f.read()

            titulo = regiao
            match = re.search(r'title.*?:\s*"(.*?)"', config_raw)
            if match:
                titulo = match.group(1)

            locais = []

            for item in os.listdir(path_regiao):
                path_local = os.path.join(path_regiao, item)

                if not os.path.isdir(path_local):
                    continue

                js_path = os.path.join(path_local, f"{item}.js")
                if not os.path.exists(js_path):
                    continue

                with open(js_path, "r", encoding="utf-8") as f:
                    raw = f.read()

                nome = item
                desc = ""

                m1 = re.search(r'title.*?:\s*"(.*?)"', raw)
                m2 = re.search(r'description.*?:\s*"(.*?)"', raw)

                if m1:
                    nome = m1.group(1)
                if m2:
                    desc = m2.group(1)

                locais.append({
                    "id": item,
                    "nome": nome,
                    "descricao": desc
                })

            resultado.append({
                "regiao": regiao,
                "titulo": titulo,
                "locais": locais
            })

        return jsonify({"success": True, "data": resultado})

    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})

# =========================
# UPLOAD ZIP
# =========================
@app.route('/api/upload_zip', methods=['POST'])
@login_required
def upload_zip():
    try:
        file = request.files['file']

        os.makedirs("pendentes", exist_ok=True)
        path = os.path.join("pendentes", file.filename)

        file.save(path)
        manager.processar_lote()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})

# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)
