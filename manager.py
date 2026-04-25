import os
import json
import re
import shutil
from js_reader import ler_js

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SiteManager:
    def __init__(self):
        self.base = os.path.join(BASE_DIR, "dados", "circuitos")

    # ── UTIL ──────────────────────────────────────────────
    def sanitizar(self, texto):
        return re.sub(r'[^a-z0-9_]', '', (texto or "").lower().replace(" ", "_"))

    def garantir_regiao(self, regiao):
        path = os.path.join(self.base, regiao)
        os.makedirs(path, exist_ok=True)
        return path

    def salvar_json(self, path, obj):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    def carregar_json(self, path):
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("💥 ERRO JSON:", path, e)
            return None

    def carregar_config(self, path_regiao):
        """config.json (manager) tem prioridade; cai em config.js (legado)."""
        return (
            self.carregar_json(os.path.join(path_regiao, "config.json")) or
            ler_js(os.path.join(path_regiao, "config.js")) or
            None
        )

    def carregar_local(self, path_local, local_id):
        """local.json (manager) tem prioridade; cai em {local_id}.js (legado)."""
        return (
            self.carregar_json(os.path.join(path_local, "local.json")) or
            ler_js(os.path.join(path_local, f"{local_id}.js"))
        )

    # ── LISTAR ────────────────────────────────────────────
    def listar(self):
        data = []

        if not os.path.exists(self.base):
            return data

        for regiao in sorted(os.listdir(self.base)):
            path_regiao = os.path.join(self.base, regiao)
            if not os.path.isdir(path_regiao):
                continue

            config = self.carregar_config(path_regiao)
            if not config:
                print(f"⚠️ Config inválido: {regiao}")
                continue

            textos = config.get("texts", {}).get("pt", {})

            regiao_obj = {
                "regiao":    config.get("id", regiao),
                "titulo":    textos.get("title", ""),
                "descricao": textos.get("subtitle", ""),
                "capa":      config.get("cover", ""),
                "texts":     config.get("texts", {}),
                "locais":    []
            }

            for item in sorted(os.listdir(path_regiao)):
                path_local = os.path.join(path_regiao, item)
                if not os.path.isdir(path_local):
                    continue

                local = self.carregar_local(path_local, item)
                if not local:
                    continue

                textos_local = local.get("texts", {}).get("pt", {})

                regiao_obj["locais"].append({
                    "id":            local.get("id", item),
                    "nome":          textos_local.get("title", ""),
                    "subtitulo":     textos_local.get("subtitle", ""),
                    "capa":          local.get("hero", ""),
                    "fotos":         local.get("gallery", []),
                    "texts":         local.get("texts", {}),
                    "location":      local.get("location", {}),
                    "RAvisionScreen": local.get("RAvisionScreen", False),
                    "RAvisionlink":  local.get("RAvisionlink", "")
                })

            data.append(regiao_obj)

        return data

    # ── CREATE / UPDATE ───────────────────────────────────
    def criar_ou_atualizar(self, payload):
        tipo = payload.get("tipo")
        if tipo == "regiao":
            self._upsert_regiao(payload)
        elif tipo == "local":
            self._upsert_local(payload)

    salvar = criar_ou_atualizar

    def _upsert_regiao(self, payload):
        regiao = self.sanitizar(payload.get("regiao"))
        path   = self.garantir_regiao(regiao)
        dados  = payload.get("dados", {})

        config_path = os.path.join(path, "config.json")
        existente   = self.carregar_config(path) or {}

        # Cover: só substitui se um novo arquivo foi enviado
        cover = payload.get("cover_file", "") or existente.get("cover", "")

        obj = {
            "id":    regiao,
            "cover": cover,
            "texts": dados.get("texts", {}) or existente.get("texts", {})
        }

        self.salvar_json(config_path, obj)

    def _upsert_local(self, payload):
        regiao      = self.sanitizar(payload.get("regiao"))
        local       = self.sanitizar(payload.get("local"))
        path_regiao = self.garantir_regiao(regiao)
        path_local  = os.path.join(path_regiao, local)
        os.makedirs(path_local, exist_ok=True)

        dados = payload.get("dados", {})

        # BUG 1 — renomeia 'desc' para 'description' em cada idioma
        texts = dados.get("texts", {})
        for lang, t in texts.items():
            if isinstance(t, dict) and "desc" in t and "description" not in t:
                t["description"] = t.pop("desc")

        # BUG 2 — auto-gera location.qr e location.embed
        location = dict(dados.get("location", {}))
        maps_url = location.get("maps", "")

        if maps_url and "qr" not in location:
            location["qr"] = (
                "https://api.qrserver.com/v1/create-qr-code/"
                f"?size=200x200&data={maps_url}"
            )

        if maps_url and "embed" not in location:
            if "/maps/search/" in maps_url:
                q = maps_url.split("/maps/search/")[-1].split("?")[0]
                embed = f"https://maps.google.com/maps?q={q}&output=embed"
            elif "q=" in maps_url:
                embed = maps_url + "&output=embed"
            else:
                embed = maps_url
            location["embed"] = embed

        obj = {
            "id":             local,
            "hero":           payload.get("cover_file", ""),
            "gallery":        dados.get("gallery", []),
            "texts":          texts,
            "location":       location,
            "RAvisionScreen": dados.get("RAvisionScreen", False),
            "RAvisionlink":   dados.get("RAvisionlink", "")
        }

        self.salvar_json(os.path.join(path_local, "local.json"), obj)

    # ── DELETE ────────────────────────────────────────────
    def deletar(self, payload):
        tipo = payload.get("tipo")

        if tipo == "regiao":
            regiao = self.sanitizar(payload.get("regiao"))
            path   = os.path.join(self.base, regiao)
            if os.path.exists(path):
                shutil.rmtree(path)

        elif tipo == "local":
            regiao = self.sanitizar(payload.get("regiao"))
            local  = self.sanitizar(payload.get("local"))
            path   = os.path.join(self.base, regiao, local)
            if os.path.exists(path):
                shutil.rmtree(path)
