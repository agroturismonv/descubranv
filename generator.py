import os
import re
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "controller.js")


# =========================================================
# PARSER ROBUSTO
# =========================================================
def parse_js_object(content, origem=""):
    """
    Extrai objeto de:
    window.APP_CONFIG = Object.freeze({...});
    """

    match = re.search(r'Object\.freeze\((\{.*\})\)', content, re.DOTALL)
    if not match:
        print(f"[ERRO] Object.freeze não encontrado: {origem}")
        return None

    obj_src = match.group(1)

    try:
        # remove comentários
        obj_src = re.sub(r'//.*', '', obj_src)

        # remove trailing commas
        obj_src = re.sub(r',(\s*[}\]])', r'\1', obj_src)

        # coloca aspas nas chaves
        obj_src = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj_src)

        # aspas simples -> duplas
        obj_src = obj_src.replace("'", '"')

        return json.loads(obj_src)

    except Exception as e:
        print(f"[ERRO PARSER] {origem}: {e}")
        return None


def carregar_js(path):
    if not os.path.exists(path):
        print(f"[ERRO] Arquivo inexistente: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return parse_js_object(f.read(), path)
    except Exception as e:
        print(f"[ERRO LEITURA] {path}: {e}")
        return None


# =========================================================
# SALVA JS
# =========================================================
def salvar_js(path, objeto, nome_objeto):
    body = json.dumps(objeto, indent=2, ensure_ascii=False)

    # estilo JS sem aspas nas chaves
    body = re.sub(r'"(\w+)":', r'\1:', body)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"window.{nome_objeto} = Object.freeze({body});\n")


# =========================================================
# BUILD PRINCIPAL
# =========================================================
def build():
    controller = {"regioes": []}

    if not os.path.isdir(DADOS_DIR):
        print("[WARN] pasta dados/circuitos não existe")
        return

    for regiao_id in sorted(os.listdir(DADOS_DIR)):
        path_regiao = os.path.join(DADOS_DIR, regiao_id)

        if not os.path.isdir(path_regiao):
            continue

        config_path = os.path.join(path_regiao, "config.js")
        config = carregar_js(config_path)

        if not config:
            print(f"[WARN] Região ignorada: {regiao_id}")
            continue

        locais_validos = []
        locais_ids = []

        # -------------------------------------------------
        # varre pastas reais da região
        # -------------------------------------------------
        for item in sorted(os.listdir(path_regiao)):
            local_dir = os.path.join(path_regiao, item)
            local_js = os.path.join(local_dir, f"{item}.js")

            if not (os.path.isdir(local_dir) and os.path.isfile(local_js)):
                continue

            local = carregar_js(local_js)

            if not local:
                print(f"[LIXO] local inválido ignorado: {regiao_id}/{item}")
                continue

            # valida id
            if local.get("id") != item:
                print(f"[ERRO] id divergente: pasta={item}, js={local.get('id')}")
                continue

            # corrige hero se vazio
            if not local.get("hero"):
                imagens_dir = os.path.join(local_dir, "images")
                if os.path.isdir(imagens_dir):
                    arquivos = sorted(os.listdir(imagens_dir))
                    if arquivos:
                        local["hero"] = f"dados/circuitos/{regiao_id}/{item}/images/{arquivos[0]}"

            locais_ids.append(item)

            locais_validos.append({
                "id": local.get("id"),
                "hero": local.get("hero", ""),
                "texts": local.get("texts", {}),
                "location": local.get("location", {}),
                "gallery": local.get("gallery", []),
                "RAvisionScreen": local.get("RAvisionScreen", False),
                "RAvisionlink": local.get("RAvisionlink", "")
            })

        # -------------------------------------------------
        # corrige config.js automaticamente
        # -------------------------------------------------
        config["id"] = regiao_id
        config["locais"] = locais_ids

        if not config.get("cover"):
            imagens_dir = os.path.join(path_regiao, "images")
            if os.path.isdir(imagens_dir):
                arquivos = sorted(os.listdir(imagens_dir))
                if arquivos:
                    config["cover"] = f"dados/circuitos/{regiao_id}/images/{arquivos[0]}"

        salvar_js(config_path, config, "APP_CONFIG")

        # -------------------------------------------------
        # adiciona ao controller
        # -------------------------------------------------
        controller["regioes"].append({
            "id": config.get("id"),
            "cover": config.get("cover", ""),
            "texts": config.get("texts", {}),
            "locais": locais_validos
        })

    salvar_controller(controller)
    print("[OK] rebuild concluído com sucesso")


# =========================================================
# CONTROLLER FINAL
# =========================================================
def salvar_controller(controller):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    lista_circuitos = [
        {
            "id": regiao.get("id", ""),
            "cover": regiao.get("cover", ""),
            "texts": regiao.get("texts", {})
        }
        for regiao in controller.get("regioes", [])
    ]

    body_controller = json.dumps(controller, indent=2, ensure_ascii=False)
    body_lista = json.dumps(lista_circuitos, indent=2, ensure_ascii=False)

    body_controller = re.sub(r'"(\w+)":', r'\1:', body_controller)
    body_lista = re.sub(r'"(\w+)":', r'\1:', body_lista)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"window.APP_CONTROLLER = Object.freeze({body_controller});\n")
        f.write(f"window.LISTA_CIRCUITOS = Object.freeze({body_lista});\n")


# =========================================================
# EXEC
# =========================================================
if __name__ == "__main__":
    build()
