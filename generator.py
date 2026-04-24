import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


def extrair_objeto_js(content):
    start = content.find("Object.freeze(")
    if start == -1:
        return None

    start = content.find("{", start)
    if start == -1:
        return None

    count = 0
    for i in range(start, len(content)):
        if content[i] == "{":
            count += 1
        elif content[i] == "}":
            count -= 1
            if count == 0:
                return content[start:i+1]

    return None


def limpar_js_para_json(obj):
    import re

    # remove comentários
    obj = re.sub(r'//.*', '', obj)
    obj = re.sub(r'/\*.*?\*/', '', obj, flags=re.DOTALL)

    # remove vírgulas finais
    obj = re.sub(r',\s*}', '}', obj)
    obj = re.sub(r',\s*]', ']', obj)

    # adiciona aspas nas keys
    obj = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj)

    return obj


def carregar_js(path):
    if not os.path.exists(path):
        print("❌ NÃO EXISTE:", path)
        return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    obj = extrair_objeto_js(content)
    if not obj:
        print("❌ NÃO ACHOU OBJETO:", path)
        return None

    obj = limpar_js_para_json(obj)

    try:
        return json.loads(obj)
    except Exception as e:
        print("💥 ERRO JSON:", path)
        print(e)
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

    for regiao in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        print("\n📁 Região:", regiao)

        config = carregar_js(os.path.join(path_regiao, "config.js")) or {}

        locais_ids = detectar_locais(path_regiao)
        print("👉 Locais encontrados:", locais_ids)

        regiao_obj = {
            "id": config.get("id", regiao),
            "cover": config.get("cover", ""),
            "texts": config.get("texts", {}),
            "locais": []
        }

        for local_id in locais_ids:
            path_js = os.path.join(path_regiao, local_id, f"{local_id}.js")

            print("🔍 Lendo:", path_js)

            local = carregar_js(path_js)
            if not local:
                print("❌ IGNORADO:", local_id)
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
    print("\n🚀 BUILD FINALIZADO")


def salvar_controller(obj):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("window.APP_CONTROLLER = ")
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write(";")
        

if __name__ == "__main__":
    build()
