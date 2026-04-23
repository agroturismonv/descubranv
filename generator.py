import os
import re
import json


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


# -------------------------
# UTIL
# -------------------------
def parse_js_object(content):
    match = re.search(r'Object\.freeze\((\{.*\})\);?\s*$', content, flags=re.DOTALL)
    if not match:
        return None

    obj_src = match.group(1)

    # Corrige JS → JSON
    obj_src = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj_src)
    obj_src = obj_src.replace("'", '"')

    try:
        return json.loads(obj_src)
    except:
        return None


def carregar_js(path):
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return parse_js_object(f.read())
    except:
        return None


# -------------------------
# BUILD
# -------------------------
def build():
    controller = {
        "regioes": []
    }

    if not os.path.exists(DADOS_DIR):
        print("⚠️ Pasta dados não existe")
        return

    regioes = sorted(os.listdir(DADOS_DIR))

    for regiao in regioes:
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        config_path = os.path.join(path_regiao, "config.js")
        config = carregar_js(config_path)

        if not config:
            print(f"⚠️ Região ignorada (config inválido): {regiao}")
            continue

        regiao_obj = {
            "id": config.get("id"),
            "cover": config.get("cover"),
            "texts": config.get("texts", {}),
            "locais": []
        }

        locais_ids = sorted(config.get("locais", []))

        for local_id in locais_ids:
            path_local = os.path.join(path_regiao, local_id)
            path_js = os.path.join(path_local, f"{local_id}.js")

            local_data = carregar_js(path_js)

            if not local_data:
                print(f"⚠️ Local ignorado: {regiao}/{local_id}")
                continue

            regiao_obj["locais"].append({
                "id": local_data.get("id"),
                "hero": local_data.get("hero"),
                "texts": local_data.get("texts", {}),
                "location": local_data.get("location", {}),
                "gallery": local_data.get("gallery", []),
                "RAvisionScreen": local_data.get("RAvisionScreen", False),
                "RAvisionlink": local_data.get("RAvisionlink", "")
            })

        controller["regioes"].append(regiao_obj)

    salvar_controller(controller)
    print("✅ Controller gerado com sucesso")


# -------------------------
# OUTPUT
# -------------------------
def salvar_controller(obj):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    body = json.dumps(obj, indent=2, ensure_ascii=False)

    # deixa estilo JS (sem aspas nas chaves)
    body = re.sub(r'"(\w+)":', r'\1:', body)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"window.APP_CONTROLLER = Object.freeze({body});")


# -------------------------
# EXEC
# -------------------------
if __name__ == "__main__":
    build()