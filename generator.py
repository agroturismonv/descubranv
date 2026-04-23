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
        print("[WARN] Pasta dados nao existe")
        return

    for regiao in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        config_path = os.path.join(path_regiao, "config.js")
        config = carregar_js(config_path)

        if not config:
            print(f"[WARN] Regiao ignorada (config invalido): {regiao}")
            continue

        textos = config.get("texts", {})

        regiao_obj = {
            "id": config.get("id", regiao),
            "cover": config.get("cover", ""),
            "texts": textos,
            "locais": []
        }

        locais_ids = []
        locais_validos = []

        # 🔎 VARRE PASTAS REAIS (FONTE DA VERDADE)
        for item in sorted(os.listdir(path_regiao)):
            local_dir = os.path.join(path_regiao, item)
            local_js = os.path.join(local_dir, f"{item}.js")

            if not (os.path.isdir(local_dir) and os.path.isfile(local_js)):
                continue

            local_data = carregar_js(local_js)

            if not local_data:
                print(f"[LIXO] JS inválido removido: {regiao}/{item}")
                continue

            # 🚨 valida ID
            if local_data.get("id") != item:
                print(f"[ERRO] ID divergente: pasta={item} js={local_data.get('id')}")
                continue

            # 🚨 valida conteúdo mínimo
            if not local_data.get("texts"):
                print(f"[LIXO] Local sem texto ignorado: {regiao}/{item}")
                continue

            # evita duplicação
            if item in locais_ids:
                continue

            locais_ids.append(item)

            locais_validos.append({
                "id": local_data.get("id"),
                "hero": local_data.get("hero"),
                "texts": local_data.get("texts", {}),
                "location": local_data.get("location", {}),
                "gallery": local_data.get("gallery", []),
                "RAvisionScreen": local_data.get("RAvisionScreen", False),
                "RAvisionlink": local_data.get("RAvisionlink", "")
            })

        # 🔧 AUTO CORRIGE config.js
        try:
            config["locais"] = locais_ids

            novo_body = json.dumps(config, indent=2, ensure_ascii=False)
            novo_body = re.sub(r'"(\w+)":', r'\1:', novo_body)

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(f"window.APP_CONFIG = Object.freeze({novo_body});")

        except Exception as e:
            print(f"[ERRO] Falha ao corrigir config.js: {regiao} -> {e}")

        regiao_obj["locais"] = locais_validos
        controller["regioes"].append(regiao_obj)

    salvar_controller(controller)
    print("[OK] Build limpo e consistente")

# -------------------------
# OUTPUT
# -------------------------
def salvar_controller(obj):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    body = json.dumps(obj, indent=2, ensure_ascii=False)
    lista_circuitos = [
        {
            "id": regiao.get("id", ""),
            "cover": regiao.get("cover", ""),
            "texts": regiao.get("texts", {}),
        }
        for regiao in obj.get("regioes", [])
    ]
    lista_body = json.dumps(lista_circuitos, indent=2, ensure_ascii=False)

    # deixa estilo JS (sem aspas nas chaves)
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
