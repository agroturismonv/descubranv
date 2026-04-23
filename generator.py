import os
import re
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


# -------------------------
# PARSER SEGURO
# -------------------------
def parse_js_object(content):
    try:
        match = re.search(r'Object\.freeze\((\{.*\})\)', content, re.DOTALL)
        if not match:
            return None

        obj = match.group(1)

        # JS → JSON
        obj = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', obj)
        obj = obj.replace("'", '"')

        return json.loads(obj)

    except Exception as e:
        print(f"[ERRO PARSER] {e}")
        return None


def carregar_js(path):
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return parse_js_object(f.read())
    except Exception as e:
        print(f"[ERRO LOAD] {path} -> {e}")
        return None


# -------------------------
# BUILD
# -------------------------
def build():
    print("\n🔄 INICIANDO BUILD...\n")

    controller = {"regioes": []}

    if not os.path.exists(DADOS_DIR):
        print("[ERRO] Pasta dados não existe")
        return

    for regiao in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        print(f"\n📁 Região: {regiao}")

        config_path = os.path.join(path_regiao, "config.js")
        config = carregar_js(config_path)

        if not config:
            print(f"⚠️ Config inválido → reconstruindo: {regiao}")
            config = {
                "id": regiao,
                "cover": "",
                "texts": {},
                "locais": []
            }

        # 🔥 DETECTA LOCAIS REAIS (fonte da verdade)
        locais_reais = []

        for item in os.listdir(path_regiao):
            path_local = os.path.join(path_regiao, item)
            js_path = os.path.join(path_local, f"{item}.js")

            if os.path.isdir(path_local) and os.path.isfile(js_path):
                locais_reais.append(item)

        locais_reais = sorted(set(locais_reais))

        if not locais_reais:
            print(f"⚠️ Região sem locais: {regiao}")

        regiao_obj = {
            "id": config.get("id", regiao),
            "cover": config.get("cover", ""),
            "texts": config.get("texts", {}),
            "locais": []
        }

        # 🔥 PROCESSA LOCAIS
        for local_id in locais_reais:
            path_local = os.path.join(path_regiao, local_id)
            path_js = os.path.join(path_local, f"{local_id}.js")

            local_data = carregar_js(path_js)

            if not local_data:
                print(f"❌ Local inválido ignorado: {regiao}/{local_id}")
                continue

            regiao_obj["locais"].append({
                "id": local_data.get("id", local_id),
                "hero": local_data.get("hero", ""),
                "texts": local_data.get("texts", {}),
                "location": local_data.get("location", {}),
                "gallery": local_data.get("gallery", []),
                "RAvisionScreen": local_data.get("RAvisionScreen", False),
                "RAvisionlink": local_data.get("RAvisionlink", "")
            })

        # 🔥 SINCRONIZA config.js automaticamente
        config["locais"] = [l["id"] for l in regiao_obj["locais"]]

        salvar_js(config_path, config)

        controller["regioes"].append(regiao_obj)

    salvar_controller(controller)

    print("\n✅ BUILD FINALIZADO COM SUCESSO\n")


# -------------------------
# SALVAR JS
# -------------------------
def salvar_js(path, obj):
    try:
        body = json.dumps(obj, indent=2, ensure_ascii=False)
        body = re.sub(r'"(\w+)":', r'\1:', body)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"window.DATA = Object.freeze({body});")

    except Exception as e:
        print(f"[ERRO SALVAR JS] {path} -> {e}")


# -------------------------
# OUTPUT FINAL
# -------------------------
def salvar_controller(obj):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    body = json.dumps(obj, indent=2, ensure_ascii=False)

    lista = [
        {
            "id": r.get("id", ""),
            "cover": r.get("cover", ""),
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

    print("📦 controller.js atualizado")


# -------------------------
# EXEC
# -------------------------
if __name__ == "__main__":
    build()
