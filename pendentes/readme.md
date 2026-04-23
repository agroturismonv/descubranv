# 📦 PASTA `pendentes/` — COMO USAR

Esta pasta é o ponto de entrada do sistema de geração automática de páginas do **Turismo Nova Venécia**.

Tudo que for colocado aqui será processado automaticamente pelo script `manager.py`.

---

## 🚀 COMO FUNCIONA

1. Coloque um arquivo `.zip` ou `.json` dentro desta pasta
2. Execute o script:

```bash
python manager.py
```

3. O sistema irá:

   * Processar os dados
   * Criar/atualizar arquivos em `dados/circuitos/`
   * Mover imagens
   * Atualizar `config.js`
   * Remover o arquivo da pasta após sucesso ✅

---

## 📁 FORMATOS ACEITOS

### ✔️ 1. Arquivo `.zip` (RECOMENDADO)

O `.zip` deve conter:

```
config.json
imagem1.jpg
imagem2.jpg
...
```

---

### ✔️ 2. Arquivo `.json`

Pode ser usado sozinho (sem imagens), mas menos comum.

---

## 🗺️ CADASTRO DE REGIÃO

### 📌 Estrutura esperada (`config.json`):

```json
{
  "tipo": "regiao",
  "regiao": "regiao_central_nv",
  "local": "regiao_central_nv",
  "cover_file": "capa.jpg",
  "dados": {
    "hero": "capa.jpg",
    "texts": {
      "pt": {
        "title": "Região Central",
        "subtitle": "Descrição..."
      },
      "en": {
        "title": "Central Region",
        "subtitle": "Description..."
      },
      "es": {
        "title": "Región Central",
        "subtitle": "Descripción..."
      }
    },
    "gallery": []
  }
}
```

---

### ⚠️ Regras importantes:

* `tipo` deve ser `"regiao"`
* `regiao` = ID único da região
* `local` = mesmo valor da região
* `cover_file` deve existir no `.zip`
* `texts.pt.title` é obrigatório

---

## 📍 CADASTRO DE LOCAL

### 📌 Estrutura esperada (`config.json`):

```json
{
  "tipo": "local",
  "regiao": "regiao_central_nv",
  "local": "nome_do_local",
  "cover_file": "foto1.jpg",
  "dados": {
    "gallery": ["foto1.jpg", "foto2.jpg"],
    "location": {
      "maps": "https://maps.google.com/...",
      "embed": "https://maps.google.com/...&output=embed"
    },
    "texts": {
      "pt": {
        "title": "Nome do Local",
        "subtitle": "Subtítulo",
        "description": "Descrição"
      },
      "en": {
        "title": "Place Name",
        "subtitle": "Subtitle",
        "description": "Description"
      },
      "es": {
        "title": "Nombre",
        "subtitle": "Subtítulo",
        "description": "Descripción"
      }
    },
    "RAvisionScreen": true,
    "RAvisionlink": "https://link360.com"
  }
}
```

---

### ⚠️ Regras importantes:

* `tipo` deve ser `"local"`
* `regiao` deve existir previamente
* `local` deve ser único
* `gallery` deve conter os nomes das imagens do `.zip`
* `cover_file` deve estar dentro de `gallery`

---

## 🧠 PADRÕES AUTOMÁTICOS DO SISTEMA

O script irá automaticamente:

* Sanitizar nomes (ex: `São Mateus` → `sao_mateus`)
* Gerar caminhos de imagens
* Criar QR Code de localização
* Atualizar `config.js`
* Evitar duplicação de locais
* Criar estrutura de pastas

---

## ❌ ERROS COMUNS

| Erro                           | Causa                        |
| ------------------------------ | ---------------------------- |
| `'texts'`                      | JSON sem campo `dados.texts` |
| `JSONDecodeError`              | JSON mal formatado           |
| `File not found`               | imagem não está no ZIP       |
| `set is not JSON serializable` | estrutura inválida no Python |

---

## ✅ BOAS PRÁTICAS

* Use IDs simples (sem espaço, acento ou maiúscula)
* Sempre inclua imagens no `.zip`
* Revise o `config.json` antes de enviar
* Prefira usar o painel HTML para gerar os arquivos

---

## 🎯 FLUXO IDEAL

```
Painel HTML → gerar ZIP → colocar em /pendentes → rodar manager.py → pronto 🎉
```

---

## 🧑‍💻 MANUTENÇÃO

Caso algo dê erro:

* O arquivo NÃO será removido
* A mensagem será exibida no terminal
* Corrija e execute novamente

---

## 📌 OBSERVAÇÃO FINAL

Esta pasta funciona como uma **fila de processamento automático**.

Tudo que entrar aqui será tratado pelo sistema — então mantenha apenas arquivos válidos.

---
