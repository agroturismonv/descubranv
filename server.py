from flask import Flask, request, jsonify, session, send_from_directory, redirect
from functools import wraps
import os
import re
from manager import SiteManager

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

manager = SiteManager()

# =========================
# 🔐 AUTH DECORATOR
# =========================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logado"):
            return jsonify({"success": False, "erro": "não autorizado"}), 403
        return f(*args, **kwargs)
    return decorated

# =========================
# 🌐 FRONTEND
# =========================
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/admin/<path:path>")
def admin(path):
    if not session.get("logado") and not path.endswith("login.html"):
        return redirect("/admin/login.html")
    return send_from_directory("admin", path)

# =========================
# 🔐 AUTH API
# =========================
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json

    user = data.get("user")
    password = data.get("password")

    if user == "admin" and password == "Admin@NV2026!":
        session["logado"] = True
        session["user"] = user
        return jsonify({"success": True, "username": user})

    return jsonify({"success": False}), 403


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/check", methods=["GET"])
def api_check():
    return jsonify({
        "logado": bool(session.get("logado")),
        "user": session.get("user")
    })


@app.route("/api/me", methods=["GET"])
@login_required
def api_me():
    return jsonify({
        "user": session.get("user")
    })

# =========================
# 📊 DASHBOARD
# =========================
@app.route("/api/dashboard", methods=["GET"])
@login_required
def api_dashboard():
    try:
        base = os.path.join("dados", "circuitos")

        total_regioes = 0
        total_locais = 0

        if os.path.exists(base):
            for regiao in os.listdir(base):
                path_regiao = os.path.join(base, regiao)

                if not os.path.isdir(path_regiao):
                    continue

                total_regioes += 1

                for item in os.listdir(path_regiao):
                    if os.path.isdir(os.path.join(path_regiao, item)):
                        total_locais += 1

        return jsonify({
            "total_locais": total_locais,
            "total_regioes": total_regioes,
            "status": "ok"
        })

    except Exception as e:
        return jsonify({
            "total_locais": 0,
            "total_regioes": 0,
            "status": "erro",
            "erro": str(e)
        })

# =========================
# 📋 LISTAR
# =========================
@app.route('/api/listar', methods=['GET'])
@login_required
def listar():
    try:
        base = os.path.join("dados", "circuitos")
        resultado = []

        if not os.path.exists(base):
            return jsonify({"success": True, "data": []})

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
# 💾 CADASTRO
# =========================
@app.route('/api/cadastro', methods=['POST'])
@login_required
def cadastro():
    try:
        payload = request.json
        manager.criar_ou_atualizar(payload)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})

# =========================
# 🗑 DELETE
# =========================
@app.route('/api/delete', methods=['POST'])
@login_required
def delete():
    try:
        payload = request.json
        manager.deletar(payload)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})

# =========================
# 📦 UPLOAD ZIP
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
# 🔁 REBUILD
# =========================
@app.route('/api/rebuild', methods=['POST'])
@login_required
def rebuild():
    try:
        manager.processar_lote()
        return jsonify({"success": True, "message": "Rebuild executado com sucesso 🚀"})
    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})

# =========================
# ▶️ RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)
