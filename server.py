from flask import Flask, request, jsonify
import os, json, shutil
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__, static_folder=".", static_url_path="")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")


# ───────────────────────────────
# UTIL
# ───────────────────────────────
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def slug(txt):
    return (
        txt.lower()
        .replace(" ", "_")
        .encode("ascii", "ignore")
        .decode()
    )


def run_build():
    try:
        subprocess.run(["python", "build.py"], check=True)
    except:
        print("⚠️ Falha ao rodar build.py")


# ───────────────────────────────
# GERAR JS
# ───────────────────────────────
def salvar_config(regiao_id, dados, cover_path):
    path = os.path.join(DADOS_DIR, regiao_id, "config.js")

    obj = {
        "id": regiao_id,
        "cover": cover_path,
        "texts": dados.get("texts", {}),
        "locais": dados.get("locais", [])
    }

    content = json.dumps(obj, indent=2, ensure_ascii=False)
    content = content.replace('"', '"')

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"window.CONFIG_{regiao_id.upper()} = Object.freeze({content});")


def salvar_local(regiao_id, local_id, dados, hero, gallery):
    pasta = os.path.join(DADOS_DIR, regiao_id, local_id)
    path = os.path.join(pasta, f"{local_id}.js")

    obj = {
        "id": local_id,
        "hero": hero,
        "gallery": gallery,
        "texts": dados.get("texts", {}),
        "location": dados.get("location", {}),
        "RAvisionScreen": dados.get("RAvisionScreen", False),
        "RAvisionlink": dados.get("RAvisionlink", "")
    }

    content = json.dumps(obj, indent=2, ensure_ascii=False)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"window.LOCAL_{local_id.upper()} = Object.freeze({content});")


# ───────────────────────────────
# CADASTRO
# ───────────────────────────────
@app.route("/api/cadastro", methods=["POST"])
def cadastro():

    raw = request.form.get("json")
    if not raw:
        return jsonify(success=False, erro="JSON não enviado")

    body = json.loads(raw)
    files = request.files.getlist("files")

    tipo = body.get("tipo")

    # ───────── REGIÃO ─────────
    if tipo == "regiao":

        regiao = slug(body.get("regiao"))
        dados = body.get("dados", {})

        pasta = os.path.join(DADOS_DIR, regiao)
        ensure_dir(pasta)

        cover_path = ""

        for f in files:
            name = secure_filename(f.filename)
            save_path = os.path.join(pasta, name)
            f.save(save_path)
            cover_path = f"dados/circuitos/{regiao}/{name}"

        salvar_config(regiao, dados, cover_path)

        run_build()
        return jsonify(success=True)

    # ───────── LOCAL ─────────
    elif tipo == "local":

        regiao = slug(body.get("regiao"))
        local = slug(body.get("local"))
        dados = body.get("dados", {})

        pasta = os.path.join(DADOS_DIR, regiao, local)
        ensure_dir(pasta)

        gallery = []

        for f in files:
            name = secure_filename(f.filename)
            save_path = os.path.join(pasta, name)
            f.save(save_path)
            gallery.append(f"dados/circuitos/{regiao}/{local}/{name}")

        hero = gallery[0] if gallery else ""

        salvar_local(regiao, local, dados, hero, gallery)

        # atualizar config.js (adiciona local)
        config_path = os.path.join(DADOS_DIR, regiao, "config.js")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                txt = f.read()

            if local not in txt:
                txt = txt.replace("locais: [", f'locais: ["{local}", ')
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(txt)

        run_build()
        return jsonify(success=True)

    return jsonify(success=False)


# ───────────────────────────────
# DELETE
# ───────────────────────────────
@app.route("/api/delete", methods=["POST"])
def delete():

    body = request.json
    tipo = body.get("tipo")

    if tipo == "local":
        regiao = body.get("regiao")
        local = body.get("local")

        path = os.path.join(DADOS_DIR, regiao, local)
        if os.path.exists(path):
            shutil.rmtree(path)

    elif tipo == "regiao":
        regiao = body.get("regiao")

        path = os.path.join(DADOS_DIR, regiao)
        if os.path.exists(path):
            shutil.rmtree(path)

    run_build()
    return jsonify(success=True)


# ───────────────────────────────
# RUN
# ───────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
