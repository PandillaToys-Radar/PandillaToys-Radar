import os
import requests

API = "https://www.rihappy.com.br/api/catalog_system/pub/products/search"

HEADERS = {
"User-Agent": "Mozilla/5.0",
"Accept": "application/json"
}

def buscar():
r = requests.get(API, params={"_from": 0, "_to": 0}, headers=HEADERS, timeout=30)
print("Status API:", r.status_code)
r.raise_for_status()
dados = r.json()
produto = dados[0]
nome = produto.get("productName", "Produto sem nome")
link = produto.get("link", "")
imagem = None
preco = None

```
for item in produto.get("items", []):
    imagens = item.get("images", [])
    if imagens:
        imagem = imagens[0].get("imageUrl") or imagens[0].get("imageText")

    sellers = item.get("sellers", [])
    for seller in sellers:
        oferta = seller.get("commertialOffer", {})
        preco = oferta.get("Price")
        if preco:
            break

    if preco:
        break

if link.startswith("/"):
    link = "https://www.rihappy.com.br" + link

return nome, link, preco, imagem
```

def enviar(nome, link, preco, imagem):
token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

```
print("Produto:", nome)
print("Preço:", preco)
print("Imagem encontrada:", bool(imagem))
print("Imagem:", imagem)

if not token:
    print("ERRO: token do Telegram não encontrado.")
    return

if not chat_id:
    print("ERRO: chat ID do Telegram não encontrado.")
    return

if not imagem:
    print("ERRO: imagem não encontrada.")
    return

telegram = "https://api.telegram.org/bot" + token + "/sendPhoto"

legenda = "TESTE DE IMAGEM - PANDILLA TOYS RADAR\n\n" + nome + "\n\nPreco: R$ " + str(preco) + "\n\n" + link

r = requests.post(
    telegram,
    data={
        "chat_id": chat_id,
        "photo": imagem,
        "caption": legenda
    },
    timeout=60
)

print("Status Telegram:", r.status_code)
print(r.text)

if r.ok:
    print("TESTE DE IMAGEM ENVIADO COM SUCESSO!")
else:
    print("ERRO AO ENVIAR A IMAGEM.")
```

def main():
nome, link, preco, imagem = buscar()
enviar(nome, link, preco, imagem)

main()
