import os
import json
import re

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR   = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


# ── JS HELPERS ────────────────────────────────────────────

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
    # Remove comentários de bloco
    obj = re.sub(r'/\*.*?\*/', '', obj, flags=re.DOTALL)
    # Remove comentários de linha, mas NÃO protocolo :// (https://, http://)
    obj = re.sub(r'(?<!:)//(?!/).*', '', obj)
    # Remove vírgulas finais
    obj = re.sub(r',\s*}', '}', obj)
    obj = re.sub(r',\s*]', ']', obj)
    # Adiciona aspas nas chaves JS
    obj = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj)
    # Converte strings com aspas simples para aspas duplas
    obj = re.sub(r"'([^']*)'", r'"\1"', obj)
    return obj


def carregar_js(path):
    if not os.path.exists(path):
        print("❌ NÃO EXISTE:", path)
        return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Normaliza line endings (Windows CRLF → LF)
    content = content.replace("\r\n", "\n").replace("\r", "")

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


def carregar_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("💥 ERRO JSON:", path, e)
        return None


# ── CARREGADORES COM FALLBACK ─────────────────────────────
# Prioridade: .json (criado pelo manager) → .js (legado)

def carregar_config(path_regiao):
    """config.json (manager) tem prioridade; cai em config.js (legado)."""
    data = carregar_json(os.path.join(path_regiao, "config.json"))
    if data:
        return data
    return carregar_js(os.path.join(path_regiao, "config.js")) or {}


def carregar_local(path_local, local_id):
    """local.json (manager) tem prioridade; cai em {local_id}.js (legado)."""
    data = carregar_json(os.path.join(path_local, "local.json"))
    if data:
        return data
    return carregar_js(os.path.join(path_local, f"{local_id}.js"))


# ── DETECÇÃO DE LOCAIS ────────────────────────────────────

def detectar_locais(path_regiao):
    """Detecta subpastas que têm local.json (manager) OU {item}.js (legado)."""
    locais = []
    for item in os.listdir(path_regiao):
        local_dir = os.path.join(path_regiao, item)
        if not os.path.isdir(local_dir):
            continue
        has_json = os.path.isfile(os.path.join(local_dir, "local.json"))
        has_js   = os.path.isfile(os.path.join(local_dir, f"{item}.js"))
        if has_json or has_js:
            locais.append(item)
    return sorted(locais)


# ── BUILD ─────────────────────────────────────────────────

def build():
    controller = {"regioes": []}

    for regiao in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        print("\n📁 Região:", regiao)

        config = carregar_config(path_regiao)

        locais_ids = detectar_locais(path_regiao)
        print("👉 Locais encontrados:", locais_ids)

        regiao_obj = {
            "id":     config.get("id", regiao),
            "cover":  config.get("cover", ""),
            "texts":  config.get("texts", {}),
            "locais": []
        }

        for local_id in locais_ids:
            path_local = os.path.join(path_regiao, local_id)
            print("🔍 Lendo:", path_local)

            local = carregar_local(path_local, local_id)
            if not local:
                print("❌ IGNORADO:", local_id)
                continue

            regiao_obj["locais"].append({
                "id":            local.get("id", local_id),
                "hero":          local.get("hero", ""),
                "texts":         local.get("texts", {}),
                "location":      local.get("location", {}),
                "gallery":       local.get("gallery", []),
                "RAvisionScreen": local.get("RAvisionScreen", False),
                "RAvisionlink":  local.get("RAvisionlink", "")
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
