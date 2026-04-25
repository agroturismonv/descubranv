import os
import json
from js_reader import ler_js

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR   = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


# ── UTIL ────────────────────────────────────────────────

def normalizar_path(path):
    """Garante que todos os caminhos funcionem no front"""
    if not path:
        return path

    path = path.replace("\\", "/")

    if path.startswith("http"):
        return path

    return "../" + path.lstrip("/")


def normalizar_lista(lista):
    return [normalizar_path(item) for item in lista or []]


def normalizar_location(location):
    if not isinstance(location, dict):
        return {}

    loc = dict(location)

    if "qr" in loc:
        loc["qr"] = normalizar_path(loc["qr"])

    if "embed" in loc:
        loc["embed"] = normalizar_path(loc["embed"])

    return loc


def carregar_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"💥 ERRO JSON: {path}\n   {e}")
        return None


def carregar_config(path_regiao):
    return (
        carregar_json(os.path.join(path_regiao, "config.json")) or
        ler_js(os.path.join(path_regiao, "config.js")) or
        {}
    )


def carregar_local(path_local, local_id):
    return (
        carregar_json(os.path.join(path_local, "local.json")) or
        ler_js(os.path.join(path_local, f"{local_id}.js"))
    )


def detectar_locais(path_regiao):
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


# ── BUILD ───────────────────────────────────────────────

def build():
    regioes = []

    if not os.path.exists(DADOS_DIR):
        print("❌ Pasta dados/circuitos não encontrada")
        return

    for regiao in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path_regiao):
            continue

        print(f"\n📁 Região: {regiao}")

        config     = carregar_config(path_regiao)
        locais_ids = detectar_locais(path_regiao)

        print("👉 Locais:", locais_ids)

        regiao_obj = {
            "id":     config.get("id", regiao),
            "cover":  normalizar_path(config.get("cover", "")),
            "texts":  config.get("texts", {}),
            "locais": []
        }

        for local_id in locais_ids:
            path_local = os.path.join(path_regiao, local_id)
            local = carregar_local(path_local, local_id)

            if not local:
                print(f"❌ IGNORADO: {local_id}")
                continue

            print(f"   ✅ {local_id}")

            location = normalizar_location(local.get("location", {}))

            local_obj = {
                "id":             local.get("id", local_id),
                "hero":           normalizar_path(local.get("hero", "")),
                "texts":          local.get("texts", {}),
                "location":       location,
                "gallery":        normalizar_lista(local.get("gallery", [])),
                "RAvisionScreen": local.get("RAvisionScreen", False),
                "RAvisionlink":   local.get("RAvisionlink", "")
            }

            regiao_obj["locais"].append(local_obj)

        regioes.append(regiao_obj)

    salvar_controller(regioes)
    print("\n🚀 BUILD FINALIZADO")


# ── OUTPUT ──────────────────────────────────────────────

def salvar_controller(regioes):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        # 1. APP_CONTROLLER
        f.write("window.APP_CONTROLLER = ")
        json.dump({"regioes": regioes}, f, indent=2, ensure_ascii=False)
        f.write(";\n\n")

        # 2. LISTA_CIRCUITOS
        lista = [
            {
                "id": r["id"],
                "cover": r["cover"],
                "texts": r["texts"]
            }
            for r in regioes
        ]

        f.write("window.LISTA_CIRCUITOS = ")
        json.dump(lista, f, indent=2, ensure_ascii=False)
        f.write(";\n\n")

        # 3. LOCAIS
        locais_dict = {}
        for r in regioes:
            for l in r["locais"]:
                locais_dict[l["id"]] = l

        f.write("window.LOCAIS = ")
        json.dump(locais_dict, f, indent=2, ensure_ascii=False)
        f.write(";\n\n")

        # 4. CONFIG_XXX
        for r in regioes:
            key = "CONFIG_" + r["id"].upper()

            cfg = {
                "id":     r["id"],
                "cover":  r["cover"],
                "texts":  r["texts"],
                "locais": [l["id"] for l in r["locais"]]
            }

            f.write(f"window.{key} = Object.freeze(")
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.write(");\n\n")

        # 5. EVENT
        f.write("window.dispatchEvent(new Event('locais-ready'));\n")


# ── RUN ─────────────────────────────────────────────────

if __name__ == "__main__":
    build()
