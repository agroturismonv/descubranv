import os
import re
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


def parse_js_object(content):
    match = re.search(r'Object\.freeze\((\{.*?\})\);?', content, re.DOTALL)
    if not match:
        return None

    obj = match.group(1)

    # Remove comentários
    obj = re.sub(r'//.*', '', obj)
    obj = re.sub(r'/\*.*?\*/', '', obj, flags=re.DOTALL)

    # Remove trailing commas
    obj = re.sub(r',\s*}', '}', obj)
    obj = re.sub(r',\s*]', ']', obj)

    # Converte keys sem aspas → "key":
    obj = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj)

    # 🔥 PROTEGE strings com aspas simples
    def proteger_strings(match):
        texto = match.group(0)
        texto = texto.replace('"', '\\"')  # escapa aspas duplas internas
        return texto

    # protege strings entre aspas simples
    obj = re.sub(r"'([^']*)'", lambda m: '"' + proteger_strings(m.group(1)) + '"', obj)

    try:
        return json.loads(obj)
    except Exception as e:
        print("[ERRO PARSE]", e)
        return None


def carregar_js(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return parse_js_object(f.read())
    except:
        return None


def detectar_locais(path_regiao):
    locais = []

    for item in os.listdir(path_regiao):
        local_dir = os.path.join(path_regiao, item)

        if not os.path.isdir(local_dir):
            continue

        js_file = os.path.join(local_dir, f"{item}.js")

        if os.path.isfile(js_file):
            locais.append(item)

    return sorted(locais)


def build():
    controller = {"regioes": []}

    if not os.path.exists(DADOS_DIR):
        print("[ERRO] pasta não existe")
        return

    for regiao in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        config = carregar_js(os.path.join(path_regiao, "config.js")) or {}

        locais_reais = detectar_locais(path_regiao)

        regiao_obj = {
            "id": config.get("id", regiao),
            "cover": config.get("cover", ""),
            "texts": config.get("texts", {}),
            "locais": []
        }

        for local_id in locais_reais:
            path_js = os.path.join(path_regiao, local_id, f"{local_id}.js")

            local = carregar_js(path_js)
            if not local:
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
    print("[OK] build concluído")


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

    body = re.sub(r'"(\w+)":', r'\1:', body)
    lista_body = re.sub(r'"(\w+)":', r'\1:', lista_body)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"window.APP_CONTROLLER = Object.freeze({body});\n")
        f.write(f"window.LISTA_CIRCUITOS = Object.freeze({lista_body});")


if __name__ == "__main__":
    build()
