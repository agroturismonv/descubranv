import os
import json
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SiteManager:
    def __init__(self):
        # CORRIGIDO: usa __file__ em vez de os.getcwd() para ser
        # invariante ao diretório de trabalho do processo (Gunicorn, etc.)
        self.base = os.path.join(BASE_DIR, "dados", "circuitos")

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

    nome_arquivo = os.path.basename(path).replace(".js", "").upper()

    # CONFIG ou LOCAL
    if nome_arquivo == "CONFIG":
        nome_pasta = os.path.basename(os.path.dirname(path)).upper()
        var_name = f"CONFIG_{nome_pasta}"
    else:
        var_name = f"LOCAL_{nome_arquivo}"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"window.{var_name} = Object.freeze({body});")

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
        except Exception as e:
            print("[ERRO PARSE]", path, e)
            return None

    # -------------------------
    # LISTAR
    # -------------------------
    def listar(self):
        data = []
        if not os.path.exists(self.base):
            return data

        for regiao in sorted(os.listdir(self.base)):
            path_regiao = os.path.join(self.base, regiao)
            if not os.path.isdir(path_regiao):
                continue

            config_path = os.path.join(path_regiao, "config.js")
            config = self.carregar_js_objeto(config_path)
            if not config:
                print(f"[WARN] Região ignorada (config inválido): {regiao}")
                continue

            textos = config.get("texts", {}).get("pt", {})
            regiao_obj = {
                "regiao": config.get("id", regiao),
                "titulo": textos.get("title", ""),
                "descricao": textos.get("subtitle", ""),
                "capa": config.get("cover", ""),
                "texts": config.get("texts", {}),
                "locais": []
            }

            for item in sorted(os.listdir(path_regiao)):
                path_local = os.path.join(path_regiao, item)
                if not os.path.isdir(path_local):
                    continue
                path_js = os.path.join(path_local, f"{item}.js")
                local = self.carregar_js_objeto(path_js)
                if not local:
                    continue
                textos_local = local.get("texts", {}).get("pt", {})
                regiao_obj["locais"].append({
                    "id": local.get("id", item),
                    "nome": textos_local.get("title", ""),
                    "subtitulo": textos_local.get("subtitle", ""),
                    "capa": local.get("hero", ""),
                    "fotos": local.get("gallery", []),
                    "texts": local.get("texts", {}),
                    "location": local.get("location", {}),
                    "RAvisionScreen": local.get("RAvisionScreen", False),
                    "RAvisionlink": local.get("RAvisionlink", "")
                })

            data.append(regiao_obj)

        return data

    # -------------------------
    # CREATE / UPDATE
    # -------------------------
    def criar_ou_atualizar(self, payload):
        tipo = payload.get("tipo")
        if tipo == "regiao":
            self._upsert_regiao(payload)
        elif tipo == "local":
            self._upsert_local(payload)

    # Alias mantido por compatibilidade caso haja chamadas externas
    salvar = criar_ou_atualizar

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
                shutil.rmtree(path)
        elif tipo == "local":
            regiao = self.sanitizar(payload.get("regiao"))
            local = self.sanitizar(payload.get("local"))
            path = os.path.join(self.base, regiao, local)
            if os.path.exists(path):
                shutil.rmtree(path)
