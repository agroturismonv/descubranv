import os
import json
import shutil
import zipfile
import re
import unicodedata
from generator import build


class SiteManager:

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dados_dir = os.path.join(self.base_dir, "dados", "circuitos")
        self.pendentes_dir = os.path.join(self.base_dir, "pendentes")

        os.makedirs(self.pendentes_dir, exist_ok=True)

    # -------------------------
    # UTIL
    # -------------------------
    def sanitizar(self, texto):
        if not texto:
            return ""
        nfkd = unicodedata.normalize("NFKD", str(texto).lower().strip())
        texto = "".join(c for c in nfkd if not unicodedata.combining(c))
        return re.sub(r'[^a-z0-9]+', '_', texto)

    def salvar_js(self, path, var_name, obj):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        body = json.dumps(obj, indent=2, ensure_ascii=False)
        body = re.sub(r'"(\w+)":', r'\1:', body)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"window.{var_name} = Object.freeze({body});")

    def parse_js_object(self, content):
        match = re.search(r'Object\.freeze\((\{.*\})\);?\s*$', content, flags=re.DOTALL)
        if not match:
            return {}

        obj_src = match.group(1)
        obj_src = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj_src)
        obj_src = obj_src.replace("'", '"')

        try:
            return json.loads(obj_src)
        except:
            return {}

    def carregar_js_objeto(self, path):
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return self.parse_js_object(f.read())
        except:
            return {}

    def merge_dict(self, base, update):
        if not isinstance(base, dict):
            return update
        for k, v in (update or {}).items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = self.merge_dict(base[k], v)
            elif v is not None:
                base[k] = v
        return base

    # -------------------------
    # CORE
    # -------------------------
    def garantir_regiao(self, regiao_slug):
        path = os.path.join(self.dados_dir, regiao_slug)
        os.makedirs(os.path.join(path, "images"), exist_ok=True)

        config_path = os.path.join(path, "config.js")

        if not os.path.exists(config_path):
            config = {
                "id": regiao_slug,
                "cover": "",
                "texts": {},
                "locais": []
            }
            self.salvar_js(config_path, f"CONFIG_{regiao_slug.upper()}", config)

        return path

    def registrar_local(self, path_regiao, local_slug):
        config_path = os.path.join(path_regiao, "config.js")
        config = self.carregar_js_objeto(config_path)

        locais = config.get("locais", [])
        if local_slug not in locais:
            locais.append(local_slug)

        config["locais"] = locais
        self.salvar_js(config_path, f"CONFIG_{config.get('id').upper()}", config)

    def remover_local(self, path_regiao, local_slug):
        config_path = os.path.join(path_regiao, "config.js")
        config = self.carregar_js_objeto(config_path)

        config["locais"] = [l for l in config.get("locais", []) if l != local_slug]

        self.salvar_js(config_path, f"CONFIG_{config.get('id').upper()}", config)

    # -------------------------
    # API DIRETA (ESSENCIAL)
    # -------------------------
    def criar_ou_atualizar(self, payload):
        tipo = payload.get("tipo")
        modo = payload.get("modo", "create")

        regiao = self.sanitizar(payload.get("regiao"))
        local = self.sanitizar(payload.get("local"))

        dados = payload.get("dados", {})
        cover = payload.get("cover_file")

        path_regiao = self.garantir_regiao(regiao)

        # -------- REGIÃO --------
        if tipo == "regiao":

            config_path = os.path.join(path_regiao, "config.js")
            existente = self.carregar_js_objeto(config_path)

            novo = {
                "id": regiao,
                "cover": f"dados/circuitos/{regiao}/images/{cover}" if cover else existente.get("cover", ""),
                "texts": dados.get("texts", {}),
                "locais": existente.get("locais", [])
            }

            final = self.merge_dict(existente, novo)
            self.salvar_js(config_path, f"CONFIG_{regiao.upper()}", final)

        # -------- LOCAL --------
        elif tipo == "local":

            path_local = os.path.join(path_regiao, local)
            path_js = os.path.join(path_local, f"{local}.js")
            os.makedirs(os.path.join(path_local, "images"), exist_ok=True)

            existente = self.carregar_js_objeto(path_js)

            base_img = f"dados/circuitos/{regiao}/{local}/images/"

            novo = {
                "id": local,
                "hero": base_img + cover if cover else existente.get("hero", ""),
                "gallery": [base_img + i for i in dados.get("gallery", [])] or existente.get("gallery", []),
                "location": dados.get("location", existente.get("location", {})),
                "texts": dados.get("texts", {}),
                "RAvisionScreen": dados.get("RAvisionScreen", False),
                "RAvisionlink": dados.get("RAvisionlink", "")
            }

            final = self.merge_dict(existente, novo)

            self.salvar_js(path_js, f"LOCAL_{local.upper()}", final)
            self.registrar_local(path_regiao, local)

        # rebuild controller sempre
        build()

    def deletar(self, payload):
        tipo = payload.get("tipo")

        regiao = self.sanitizar(payload.get("regiao"))
        local = self.sanitizar(payload.get("local"))

        path_regiao = os.path.join(self.dados_dir, regiao)

        if tipo == "local":
            path_local = os.path.join(path_regiao, local)

            if os.path.exists(path_local):
                shutil.rmtree(path_local)

            self.remover_local(path_regiao, local)

        elif tipo == "regiao":
            if os.path.exists(path_regiao):
                shutil.rmtree(path_regiao)

        build()

    # -------------------------
    # LOTE (MANTIDO)
    # -------------------------
    def processar_lote(self):
        arquivos = [f for f in os.listdir(self.pendentes_dir) if f.endswith((".json", ".zip"))]

        for arquivo in arquivos:
            caminho = os.path.join(self.pendentes_dir, arquivo)

            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    payload = json.load(f)

                if payload.get("modo") == "delete":
                    self.deletar(payload)
                else:
                    self.criar_ou_atualizar(payload)

                os.remove(caminho)

            except Exception as e:
                print(f"Erro em {arquivo}: {e}")


if __name__ == "__main__":
    SiteManager().processar_lote()