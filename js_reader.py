"""
Utilitário compartilhado: lê arquivos .js legados com Object.freeze()
e retorna um dict Python. Usado por manager.py e generator.py.
"""
import re
import json


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
                return content[start:i + 1]
    return None


def limpar_js_para_json(obj):
    # Remove comentários de bloco
    obj = re.sub(r'/\*.*?\*/', '', obj, flags=re.DOTALL)
    # Remove comentários de linha (não confunde :// de URLs)
    obj = re.sub(r'(?<!:)//(?!/).*', '', obj)
    # Remove vírgulas finais
    obj = re.sub(r',\s*}', '}', obj)
    obj = re.sub(r',\s*]', ']', obj)
    # Adiciona aspas nas chaves JS
    obj = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', obj)
    # Converte aspas simples para duplas em valores
    obj = re.sub(r"'([^']*)'", r'"\1"', obj)
    return obj


def ler_js(path):
    """Lê um arquivo .js com Object.freeze() e retorna dict ou None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return None

    content = content.replace("\r\n", "\n").replace("\r", "")
    obj = extrair_objeto_js(content)
    if not obj:
        return None

    obj = limpar_js_para_json(obj)
    try:
        return json.loads(obj)
    except Exception as e:
        print(f"💥 ERRO parse JS: {path}\n   {e}")
        return None
