from flask import Flask, request, jsonify, send_file
import os, json, zipfile
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)

DATA_FILE = "dados.json"
UPLOAD_DIR = "dados"


# ───────────────────────────────
# UTIL
# ───────────────────────────────
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def find_regiao(data, regiao_id):
    return next((r for r in data if r["regiao"] == regiao_id), None)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


# ───────────────────────────────
# CADASTRO COM UPLOAD
# ───────────────────────────────
@app.route("/api/cadastro", methods=["POST"])
def cadastro():

    data = load_data()

    # recebe JSON dentro do FormData
    raw_json = request.form.get("json")
    if not raw_json:
        return jsonify(success=False, erro="JSON não enviado")

    body = json.loads(raw_json)
    files = request.files.getlist("files")

    tipo = body.get("tipo")

    # ───────── REGIÃO ─────────
    if tipo == "regiao":

        regiao_id = body.get("regiao")
        dados = body.get("dados", {})

        pasta = os.path.join(UPLOAD_DIR, "regioes", regiao_id)
        ensure_dir(pasta)

        capa_path = None

        for f in files:
            filename = secure_filename(f.filename)
            save_path = os.path.join(pasta, filename)
            f.save(save_path)
            capa_path = f"{UPLOAD_DIR}/regioes/{regiao_id}/{filename}"

        reg = find_regiao(data, regiao_id)

        if not reg:
            reg = {
                "regiao": regiao_id,
                "titulo": dados.get("texts", {}).get("pt", {}).get("title", ""),
                "descricao": dados.get("texts", {}).get("pt", {}).get("desc", ""),
                "capa": capa_path,
                "locais": []
            }
            data.append(reg)
        else:
            reg["titulo"] = dados.get("texts", {}).get("pt", {}).get("title", "")
            reg["descricao"] = dados.get("texts", {}).get("pt", {}).get("desc", "")
            if capa_path:
                reg["capa"] = capa_path

        save_data(data)
        return jsonify(success=True)

    # ───────── LOCAL ─────────
    elif tipo == "local":

        regiao_id = body.get("regiao")
        local_id = body.get("local")
        dados = body.get("dados", {})

        reg = find_regiao(data, regiao_id)
        if not reg:
            return jsonify(success=False, erro="Região não encontrada")

        pasta = os.path.join(UPLOAD_DIR, "locais", local_id)
        ensure_dir(pasta)

        fotos_salvas = []

        for f in files:
            filename = secure_filename(f.filename)
            path = os.path.join(pasta, filename)
            f.save(path)
            fotos_salvas.append(f"{UPLOAD_DIR}/locais/{local_id}/{filename}")

        capa = fotos_salvas[0] if fotos_salvas else None

        obj = {
            "id": local_id,
            "nome": dados.get("texts", {}).get("pt", {}).get("title", ""),
            "subtitulo": dados.get("texts", {}).get("pt", {}).get("subtitle", ""),
            "descricao": dados.get("texts", {}).get("pt", {}).get("desc", ""),
            "capa": capa,
            "fotos": fotos_salvas
        }

        existente = next((l for l in reg["locais"] if l["id"] == local_id), None)

        if existente:
            reg["locais"] = [
                obj if l["id"] == local_id else l
                for l in reg["locais"]
            ]
        else:
            reg["locais"].append(obj)

        save_data(data)
        return jsonify(success=True)

    return jsonify(success=False, erro="Tipo inválido")


# ───────────────────────────────
# LISTAR
# ───────────────────────────────
@app.route("/api/listar", methods=["GET"])
def listar():
    return jsonify(success=True, data=load_data())


# ───────────────────────────────
# DELETE
# ───────────────────────────────
@app.route("/api/delete", methods=["POST"])
def delete():
    data = load_data()
    body = request.json

    tipo = body.get("tipo")

    if tipo == "regiao":
        regiao_id = body.get("regiao")

        data = [r for r in data if r["regiao"] != regiao_id]

        # remove pasta
        path = os.path.join(UPLOAD_DIR, "regioes", regiao_id)
        if os.path.exists(path):
            import shutil
            shutil.rmtree(path)

        save_data(data)
        return jsonify(success=True)

    elif tipo == "local":
        regiao_id = body.get("regiao")
        local_id = body.get("local")

        reg = find_regiao(data, regiao_id)
        if not reg:
            return jsonify(success=False)

        reg["locais"] = [l for l in reg["locais"] if l["id"] != local_id]

        path = os.path.join(UPLOAD_DIR, "locais", local_id)
        if os.path.exists(path):
            import shutil
            shutil.rmtree(path)

        save_data(data)
        return jsonify(success=True)

    return jsonify(success=False)


# ───────────────────────────────
# DOWNLOAD ZIP (COM IMAGENS)
# ───────────────────────────────
@app.route("/download_zip/<regiao>/<local>")
def download_zip(regiao, local):

    data = load_data()
    reg = find_regiao(data, regiao)
    if not reg:
        return jsonify(success=False), 404

    loc = next((l for l in reg["locais"] if l["id"] == local), None)
    if not loc:
        return jsonify(success=False), 404

    memory = BytesIO()

    with zipfile.ZipFile(memory, 'w') as zf:

        zf.writestr("config.json", json.dumps(loc, indent=2, ensure_ascii=False))

        for foto in loc.get("fotos", []):
            if os.path.exists(foto):
                zf.write(foto, os.path.basename(foto))

    memory.seek(0)

    return send_file(memory, as_attachment=True, download_name=f"{local}.zip")


# ───────────────────────────────
# SERVIR IMAGENS
# ───────────────────────────────
@app.route("/dados/<path:filename>")
def media(filename):
    return send_file(os.path.join("dados", filename))


# ───────────────────────────────
# RUN
# ───────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
