import os
import json
import re
import shutil


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

            match = re.search(r'Object\.freeze\((\{.*\})\)', content, re.DOTALL)
            if not match:
                return None

            obj = match.group(1)
            obj = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj)
            obj = obj.replace("'", '"')

            return json.loads(obj)
        except:
            return None

    # -------------------------
    # LISTAGEM (ESSENCIAL)
    # -------------------------
    def listar(self):
        resultado = []

        if not os.path.exists(self.base):
            return resultado

        for regiao in sorted(os.listdir(self.base)):
            path_regiao = os.path.join(self.base, regiao)

            if not os.path.isdir(path_regiao):
                continue

            config_path = os.path.join(path_regiao, "config.js")
            config = self.carregar_js_objeto(config_path)

            if not config:
                print(f"[ERRO] config inválido: {regiao}")
                continue

            locais = []

            # 🔥 fallback inteligente
            locais_ids = config.get("locais", [])

            if not locais_ids:
                for pasta in os.listdir(path_regiao):
                    local_path = os.path.join(path_regiao, pasta)
                    js_path = os.path.join(local_path, f"{pasta}.js")

                    if os.path.isdir(local_path) and os.path.exists(js_path):
                        locais_ids.append(pasta)

            for local in set(locais_ids):
                path_local = os.path.join(path_regiao, local)
                js_path = os.path.join(path_local, f"{local}.js")

                data = self.carregar_js_objeto(js_path)

                if not data:
                    print(f"[ERRO] local inválido: {regiao}/{local}")
                    continue

                locais.append(data)

            resultado.append({
                "regiao": regiao,
                "locais": locais,
                "config": config
            })

        return resultado

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
            "texts": dados.get("texts", {}),
            "locais": []  # 🔥 obrigatório
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

        # 🔥 atualiza config automaticamente
        config_path = os.path.join(path_regiao, "config.js")
        config = self.carregar_js_objeto(config_path) or {}

        locais = config.get("locais", [])
        if local not in locais:
            locais.append(local)

        config["locais"] = sorted(set(locais))
        self.salvar_js(config_path, config)

    # -------------------------
    # DELETE
    # -------------------------
    def deletar(self, payload):
        tipo = payload.get("tipo")

        if tipo == "regiao":
            regiao = self.sanitizar(payload.get("regiao"))
            path = os.path.join(self.base, regiao)

            if os.path.exists(path):
                shutil.rmtree(path)

        elif tipo == "local":
            regiao = self.sanitizar(payload.get("regiao"))
            local = self.sanitizar(payload.get("local"))

            path = os.path.join(self.base, regiao, local)

            if os.path.exists(path):
                shutil.rmtree(path)

            # 🔥 remove do config
            config_path = os.path.join(self.base, regiao, "config.js")
            config = self.carregar_js_objeto(config_path)

            if config:
                locais = config.get("locais", [])
                if local in locais:
                    locais.remove(local)

                config["locais"] = locais
                self.salvar_js(config_path, config)
