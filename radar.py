import os
import json
import hashlib
import requests

API = "https://www.rihappy.com.br/api/catalog_system/pub/products/search"

HEADERS = {
"User-Agent": "Mozilla/5.0",
"Accept": "application/json"
}

BANCO = "data/products.json"

def id_produto(url):
return hashlib.sha256(url.encode("utf-8")).hexdigest()

def carregar_banco():
if not os.path.exists(BANCO):
return []
with open(BANCO, "r", encoding="utf-8") as arquivo:
return json.load(arquivo)

def salvar_banco(produtos):
with open(BANCO, "w", encoding="utf-8") as arquivo:
json.dump(produtos, arquivo, ensure_ascii=False, indent=2)

def buscar_produtos():
resposta = requests.get(
API,
params={"_from": 0, "_to": 49},
headers=HEADERS,
timeout=30
)

```
print("STATUS API:", resposta.status_code)

resposta.raise_for_status()

dados = resposta.json()

produtos = []

for produto in dados:
    nome = produto.get("productName")
    link = produto.get("link")

    if not nome or not link:
        continue

    if link.startswith("/"):
        link = "https://www.rihappy.com.br" + link

    imagem = None
    preco = None

    for item in produto.get("items", []):
        imagens = item.get("images", [])

        if imagens:
            imagem = imagens[0].get("imageUrl")

        for seller in item.get("sellers", []):
            oferta = seller.get("commertialOffer", {})
            valor = oferta.get("Price")

            if valor:
                preco = float(valor)
                break

        if preco:
            break

    if preco is None:
        continue

    produtos.append({
        "id": id_produto(link),
        "nome": nome,
        "url": link,
        "preco": preco,
        "imagem": imagem,
        "loja": "Ri Happy"
    })

return produtos
```

def enviar_telegram(produto):
token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat = os.environ.get("TELEGRAM_CHAT_ID")

```
if not token or not chat:
    print("Telegram não configurado.")
    return

legenda = (
    "🆕 NOVO PRODUTO\n\n"
    "🧸 " + produto["nome"] +
    "\n\n"
    "💰 R$ " + str(produto["preco"]) +
    "\n\n"
    "🛒 Ri Happy\n\n"
    "🔗 " + produto["url"]
)

if produto["imagem"]:
    url = "https://api.telegram.org/bot" + token + "/sendPhoto"

    resposta = requests.post(
        url,
        data={
            "chat_id": chat,
            "photo": produto["imagem"],
            "caption": legenda
        },
        timeout=60
    )

    print("TELEGRAM FOTO:", resposta.status_code)

    if resposta.ok:
        return

url = "https://api.telegram.org/bot" + token + "/sendMessage"

requests.post(
    url,
    data={
        "chat_id": chat,
        "text": legenda
    },
    timeout=30
)
```

print("================================")
print("PANDILLA TOYS RADAR")
print("================================")

banco = carregar_banco()

produtos = buscar_produtos()

print("PRODUTOS ENCONTRADOS:", len(produtos))

ids_banco = set()

for produto in banco:
ids_banco.add(produto.get("id"))

novos = []

for produto in produtos:
if produto["id"] not in ids_banco:
novos.append(produto)
banco.append(produto)

salvar_banco(banco)

print("NOVOS PRODUTOS:", len(novos))

for produto in novos:
enviar_telegram(produto)

print("BANCO TOTAL:", len(banco))
print("RADAR FINALIZADO.")
