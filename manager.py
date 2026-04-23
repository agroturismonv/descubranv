import os
import re
import json
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "circuitos")


class SiteManager:

    # =========================================================
    # UTIL
    # =========================================================
    def sanitizar(self, texto):
        if not texto:
            return ""

        texto = texto.lower().strip()

        # remove acentos simples
        texto = re.sub(r'[áàãâä]', 'a', texto)
        texto = re.sub(r'[éèêë]', 'e', texto)
        texto = re.sub(r'[íìîï]', 'i', texto)
        texto = re.sub(r'[óòõôö]', 'o', texto)
        texto = re.sub(r'[úùûü]', 'u', texto)
        texto = re.sub(r'ç', 'c', texto)

        # só permite letras, numeros e _
        texto = re.sub(r'[^a-z0-9_]', '_', texto)
        texto = re.sub(r'_+', '_', texto)

        return texto.strip('_')

    def garantir_regiao(self, regiao):
        regiao = self.sanitizar(regiao)

        if not regiao:
            raise Exception("Região inválida")

        path = os.path.join(DADOS_DIR, regiao)
        os.makedirs(path, exist_ok=True)

        return path

    def garantir_local(self, regiao, local):
        regiao = self.sanitizar(regiao)
        local = self.sanitizar(local)

        if not regiao or not local:
            raise Exception("Região ou local inválido")

        path = os.path.join(DADOS_DIR, regiao, local)
        os.makedirs(path, exist_ok=True)

        return path

    def salvar_js(self, path, obj, nome):
        body = json.dumps(obj, indent=2, ensure_ascii=False)
        body = re.sub(r'"(\w+)":', r'\1:', body)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"window.{nome} = Object.freeze({body});\n")

    # =========================================================
    # CREATE / UPDATE
    # =========================================================
    def criar_ou_atualizar(self, payload):

        tipo = payload.get("tipo")

        if tipo == "regiao":
            return self._upsert_regiao(payload)

        if tipo == "local":
            return self._upsert_local(payload)

        raise Exception("Tipo inválido")

    # ---------------- REGIÃO ----------------
    def _upsert_regiao(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        dados = payload.get("dados", {})

        if not regiao:
            raise Exception("Região inválida")

        path = self.garantir_regiao(regiao)

        config_path = os.path.join(path, "config.js")

        config = {
            "id": regiao,
            "cover": payload.get("cover_file") or dados.get("cover") or "",
            "texts": dados.get("texts", {})
        }

        self.salvar_js(config_path, config, "APP_CONFIG")

    # ---------------- LOCAL ----------------
    def _upsert_local(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        local = self.sanitizar(payload.get("local"))
        dados = payload.get("dados", {})

        if not regiao or not local:
            raise Exception("Região/local inválido")

        path_local = self.garantir_local(regiao, local)

        js_path = os.path.join(path_local, f"{local}.js")

        hero = payload.get("cover_file") or dados.get("hero") or ""
        gallery = dados.get("gallery", [])

        obj = {
            "id": local,
            "hero": hero,
            "texts": dados.get("texts", {}),
            "location": dados.get("location", {}),
            "gallery": gallery,
            "RAvisionScreen": dados.get("RAvisionScreen", False),
            "RAvisionlink": dados.get("RAvisionlink", "")
        }

        self.salvar_js(js_path, obj, local)

    # =========================================================
    # DELETE
    # =========================================================
    def deletar(self, payload):
        tipo = payload.get("tipo")

        if tipo == "regiao":
            return self._delete_regiao(payload)

        if tipo == "local":
            return self._delete_local(payload)

        raise Exception("Tipo inválido")

    def _delete_regiao(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))

        path = os.path.join(DADOS_DIR, regiao)

        if not os.path.isdir(path):
            raise Exception("Região não existe")

        shutil.rmtree(path)

    def _delete_local(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        local = self.sanitizar(payload.get("local"))

        path = os.path.join(DADOS_DIR, regiao, local)

        if not os.path.isdir(path):
            raise Exception("Local não existe")

        shutil.rmtree(path)

    # =========================================================
    # LEITURA AUXILIAR (usado pelo backend)
    # =========================================================
    def carregar_js_objeto(self, path):
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            match = re.search(r'Object\.freeze\((\{.*\})\)', content, re.DOTALL)
            if not match:
                return None

            obj_src = match.group(1)

            obj_src = re.sub(r'//.*', '', obj_src)
            obj_src = re.sub(r',(\s*[}\]])', r'\1', obj_src)
            obj_src = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj_src)
            obj_src = obj_src.replace("'", '"')

            return json.loads(obj_src)

        except Exception as e:
            print(f"[ERRO LOAD JS] {path} -> {e}")
            return None
