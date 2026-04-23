import os
import json
import re


class SiteManager:
    def __init__(self):
        self.base = os.path.join(os.getcwd(), "dados", "circuitos")

    # -------------------------
    # UTIL
    # -------------------------
    def sanitizar(self, texto):
        return re.sub(r'[^a-z0-9_]', '', (texto or "").lower().replace(" ", "_"))

    def garantir_regiao(self, regiao):
        path = os.path.join(self.base, regiao)
        os.makedirs(path, exist_ok=True)
        return path

    def salvar_js(self, path, obj):
        body = json.dumps(obj, indent=2, ensure_ascii=False)
        body = re.sub(r'"(\w+)":', r'\1:', body)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"export default Object.freeze({body});")

    def carregar_js_objeto(self, path):
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            match = re.search(r'Object\.freeze\((\{.*\})\);?', content, re.DOTALL)
            if not match:
                return None

            obj = match.group(1)
            obj = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj)
            obj = obj.replace("'", '"')

            return json.loads(obj)
        except:
            return None

    # -------------------------
    # CREATE / UPDATE
    # -------------------------
    def criar_ou_atualizar(self, payload):
        tipo = payload.get("tipo")

        if tipo == "regiao":
            self._upsert_regiao(payload)

        elif tipo == "local":
            self._upsert_local(payload)

    def _upsert_regiao(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        path = self.garantir_regiao(regiao)

        dados = payload.get("dados", {})

        obj = {
            "id": regiao,
            "cover": payload.get("cover_file", ""),
            "texts": dados.get("texts", {})
        }

        self.salvar_js(os.path.join(path, "config.js"), obj)

    def _upsert_local(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        local = self.sanitizar(payload.get("local"))

        path_regiao = self.garantir_regiao(regiao)
        path_local = os.path.join(path_regiao, local)

        os.makedirs(path_local, exist_ok=True)

        dados = payload.get("dados", {})

        obj = {
            "id": local,
            "hero": payload.get("cover_file", ""),
            "gallery": dados.get("gallery", []),
            "texts": dados.get("texts", {}),
            "location": dados.get("location", {}),
            "RAvisionScreen": dados.get("RAvisionScreen", False),
            "RAvisionlink": dados.get("RAvisionlink", "")
        }

        self.salvar_js(os.path.join(path_local, f"{local}.js"), obj)

    # -------------------------
    # DELETE
    # -------------------------
    def deletar(self, payload):
        tipo = payload.get("tipo")

        if tipo == "regiao":
            regiao = self.sanitizar(payload.get("regiao"))
            path = os.path.join(self.base, regiao)

            if os.path.exists(path):
                import shutil
                shutil.rmtree(path)

        elif tipo == "local":
            regiao = self.sanitizar(payload.get("regiao"))
            local = self.sanitizar(payload.get("local"))

            path = os.path.join(self.base, regiao, local)

            if os.path.exists(path):
                import shutil
                shutil.rmtree(path)
