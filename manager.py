import os
import json
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")


class SiteManager:

    # -------------------------
    # UTIL
    # -------------------------
    def sanitizar(self, text):
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9\-]', '-', text)
        text = re.sub(r'-+', '-', text)
        return text.strip('-')

    def garantir_regiao(self, regiao):
        regiao = self.sanitizar(regiao)
        path = os.path.join(DADOS_DIR, regiao)
        os.makedirs(path, exist_ok=True)

        config_path = os.path.join(path, "config.js")

        if not os.path.exists(config_path):
            self.salvar_js(config_path, {
                "id": regiao,
                "cover": "",
                "texts": {},
                "locais": []
            })

        return path

    def salvar_js(self, path, obj):
        body = json.dumps(obj, indent=2, ensure_ascii=False)
        body = re.sub(r'"(\w+)":', r'\1:', body)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"window.DATA = Object.freeze({body});")

    def carregar_js_objeto(self, path):
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            match = re.search(r'Object\.freeze\((\{.*\})\)', content, re.DOTALL)
            if not match:
                return None

            raw = match.group(1)

            raw = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', raw)
            raw = raw.replace("'", '"')

            return json.loads(raw)
        except:
            return None

    # -------------------------
    # CORE
    # -------------------------
    def criar_ou_atualizar(self, payload):
        tipo = payload.get("tipo")

        if tipo == "regiao":
            return self._upsert_regiao(payload)

        if tipo == "local":
            return self._upsert_local(payload)

    # -------------------------
    # REGIAO
    # -------------------------
    def _upsert_regiao(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        dados = payload.get("dados", {})

        path = self.garantir_regiao(regiao)
        config_path = os.path.join(path, "config.js")

        config = self.carregar_js_objeto(config_path) or {}

        config["id"] = regiao
        config["cover"] = payload.get("cover_file", config.get("cover", ""))
        config["texts"] = dados.get("texts", config.get("texts", {}))

        config.setdefault("locais", [])

        self.salvar_js(config_path, config)

    # -------------------------
    # LOCAL
    # -------------------------
    def _upsert_local(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        local = self.sanitizar(payload.get("local"))
        dados = payload.get("dados", {})

        path_regiao = self.garantir_regiao(regiao)
        path_local = os.path.join(path_regiao, local)

        os.makedirs(path_local, exist_ok=True)

        local_path = os.path.join(path_local, f"{local}.js")

        obj = {
            "id": local,
            "hero": payload.get("cover_file", ""),
            "texts": dados.get("texts", {}),
            "location": dados.get("location", {}),
            "gallery": dados.get("gallery", []),
            "RAvisionScreen": dados.get("RAvisionScreen", False),
            "RAvisionlink": dados.get("RAvisionlink", "")
        }

        self.salvar_js(local_path, obj)

        # 🔥 sincroniza config.js
        config_path = os.path.join(path_regiao, "config.js")
        config = self.carregar_js_objeto(config_path) or {
            "id": regiao,
            "locais": []
        }

        if local not in config["locais"]:
            config["locais"].append(local)

        config["locais"] = sorted(set(config["locais"]))

        self.salvar_js(config_path, config)

    # -------------------------
    # DELETE
    # -------------------------
    def deletar(self, payload):
        tipo = payload.get("tipo")

        if tipo == "regiao":
            return self._delete_regiao(payload)

        if tipo == "local":
            return self._delete_local(payload)

    def _delete_regiao(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        path = os.path.join(DADOS_DIR, regiao)

        if os.path.exists(path):
            shutil.rmtree(path)

    def _delete_local(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        local = self.sanitizar(payload.get("local"))

        path_regiao = os.path.join(DADOS_DIR, regiao)
        path_local = os.path.join(path_regiao, local)

        if os.path.exists(path_local):
            shutil.rmtree(path_local)

        # 🔥 remove do config.js
        config_path = os.path.join(path_regiao, "config.js")
        config = self.carregar_js_objeto(config_path)

        if config and "locais" in config:
            config["locais"] = [l for l in config["locais"] if l != local]
            self.salvar_js(config_path, config)
