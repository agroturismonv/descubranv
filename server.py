from flask import Flask, request, jsonify, session, send_from_directory, redirect
from functools import wraps
from manager import SiteManager
import os

app = Flask(__name__)
app.secret_key = "super-secret-key"  # troque isso em produção

manager = SiteManager()



# -------------------------
# AUTH
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logado"):
            return jsonify({"success": False, "erro": "não autorizado"}), 403
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/admin/<path:path>")
def admin(path):
    return send_from_directory("admin", path)


#Página do leo
@app.route("/ra")
def ra():
    return send_from_directory(".", "ra.html")


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json

    user = data.get("user")
    password = data.get("password")

    # 🔴 TROCAR ISSO depois por algo mais seguro
    if user == "admin" and password == "123":
        session["logado"] = True
        return jsonify({"success": True})

    return jsonify({"success": False})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route('/api/check', methods=['GET'])
def check():
    return jsonify({"logado": bool(session.get("logado"))})


# -------------------------
# CADASTRO (CREATE / UPDATE)
# -------------------------
@app.route('/api/cadastro', methods=['POST'])
@login_required
def cadastro():
    try:
        payload = request.json
        manager.criar_ou_atualizar(payload)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})


# -------------------------
# GET PARA EDIÇÃO
# -------------------------
@app.route('/api/cadastro', methods=['GET'])
@login_required
def get_cadastro():
    try:
        tipo = request.args.get("tipo")
        regiao = request.args.get("regiao")
        local = request.args.get("local")

        base = os.path.join("dados", "circuitos", regiao)

        if tipo == "regiao":
            path = os.path.join(base, "config.js")
        else:
            path = os.path.join(base, local, f"{local}.js")

        if not os.path.exists(path):
            return jsonify({"success": False, "erro": "não encontrado"})

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return jsonify({"success": True, "raw": content})

    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})


# -------------------------
# DELETE
# -------------------------
@app.route('/api/delete', methods=['POST'])
@login_required
def delete():
    try:
        payload = request.json
        manager.deletar(payload)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})


# -------------------------
# LISTAGEM (IMPORTANTE)
# -------------------------
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

            # pegar título pt
            titulo = regiao

            match = None
            import re
            match = re.search(r'texts.*?pt.*?title.*?:\s*"(.*?)"', config_raw, re.DOTALL)
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


# -------------------------
# ZIP (já existente)
# -------------------------
@app.route('/api/upload_zip', methods=['POST'])
@login_required
def upload_zip():
    try:
        file = request.files['file']

        path = os.path.join("pendentes", file.filename)
        os.makedirs("pendentes", exist_ok=True)

        file.save(path)

        manager.processar_lote()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "erro": str(e)})


# -------------------------
# RUN
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
