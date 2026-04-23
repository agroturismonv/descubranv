import os
import re
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


# -------------------------
# PARSER JS → JSON
# -------------------------
def parse_js_object(content):
    match = re.search(r'Object\.freeze\((\{.*\})\);?', content, re.DOTALL)
    if not match:
        return None

    obj = match.group(1)

    obj = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj)
    obj = obj.replace("'", '"')

    try:
        return json.loads(obj)
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
# DETECTA LOCAIS REALMENTE EXISTENTES
# -------------------------
def detectar_locais(path_regiao):
    locais = []

    for item in os.listdir(path_regiao):
        local_dir = os.path.join(path_regiao, item)

        if not os.path.isdir(local_dir):
            continue

        js_file = os.path.join(local_dir, f"{item}.js")

        if os.path.isfile(js_file):
            locais.append(item)
        else:
            print(f"[LIXO REMOVIDO] {item} (sem JS válido)")

    return sorted(locais)


# -------------------------
# BUILD
# -------------------------
def build():
    controller = {"regioes": []}

    if not os.path.exists(DADOS_DIR):
        print("[ERRO] pasta dados/circuitos não existe")
        return

    for regiao in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        config_path = os.path.join(path_regiao, "config.js")
        config = carregar_js(config_path) or {}

        # 🔥 AUTOCORREÇÃO
        locais_reais = detectar_locais(path_regiao)

        regiao_id = config.get("id") or regiao

        regiao_obj = {
            "id": regiao_id,
            "cover": config.get("cover", ""),
            "texts": config.get("texts", {}),
            "locais": []
        }

        for local_id in locais_reais:
            path_local = os.path.join(path_regiao, local_id)
            path_js = os.path.join(path_local, f"{local_id}.js")

            local = carregar_js(path_js)

            if not local:
                print(f"[ERRO] JS inválido: {regiao}/{local_id}")
                continue

            regiao_obj["locais"].append({
                "id": local.get("id", local_id),
                "hero": local.get("hero", ""),
                "texts": local.get("texts", {}),
                "location": local.get("location", {}),
                "gallery": local.get("gallery", []),
                "RAvisionScreen": local.get("RAvisionScreen", False),
                "RAvisionlink": local.get("RAvisionlink", "")
            })

        controller["regioes"].append(regiao_obj)

    salvar_controller(controller)
    print("[OK] BUILD LIMPO E CONSISTENTE")


# -------------------------
# OUTPUT
# -------------------------
def salvar_controller(obj):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    body = json.dumps(obj, indent=2, ensure_ascii=False)

    lista = [
        {
            "id": r.get("id"),
            "cover": r.get("cover"),
            "texts": r.get("texts", {})
        }
        for r in obj.get("regioes", [])
    ]

    lista_body = json.dumps(lista, indent=2, ensure_ascii=False)

    # estilo JS
    body = re.sub(r'"(\w+)":', r'\1:', body)
    lista_body = re.sub(r'"(\w+)":', r'\1:', lista_body)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"window.APP_CONTROLLER = Object.freeze({body});\n")
        f.write(f"window.LISTA_CIRCUITOS = Object.freeze({lista_body});")


# -------------------------
# EXEC
# -------------------------
if __name__ == "__main__":
    build()
