import os
import requests

url_api = "https://www.rihappy.com.br/api/catalog_system/pub/products/search"

resposta = requests.get(
url_api,
params={"_from": 0, "_to": 0},
headers={
"User-Agent": "Mozilla/5.0",
"Accept": "application/json"
},
timeout=30
)

print("Status API:", resposta.status_code)

dados = resposta.json()

if not dados:
print("Nenhum produto encontrado.")
exit()

produto = dados[0]

nome = produto.get("productName", "Produto sem nome")
link = produto.get("link", "")
preco = None
imagem = None

for item in produto.get("items", []):

```
if imagem is None:

    imagens = item.get("images", [])

    if imagens:

        imagem = (
            imagens[0].get("imageUrl")
            or imagens[0].get("imageText")
        )

for seller in item.get("sellers", []):

    oferta = seller.get("commertialOffer", {})
    valor = oferta.get("Price")

    if valor:
        preco = valor
        break

if preco:
    break
```

if link.startswith("/"):
link = "https://www.rihappy.com.br" + link

print("Produto:", nome)
print("Preço:", preco)
print("Imagem encontrada:", bool(imagem))
print("Imagem:", imagem)

token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if not token or not chat_id:

```
print("ERRO: Telegram não configurado.")
exit()
```

if not imagem:

```
print("ERRO: produto sem imagem.")
exit()
```

telegram_url = "https://api.telegram.org/bot" + token + "/sendPhoto"

legenda = (
"TESTE DE IMAGEM - PANDILLA TOYS RADAR\n\n"
+ nome
+ "\n\nPreco: R$ "
+ str(preco)
+ "\n\n"
+ link
)

envio = requests.post(
telegram_url,
data={
"chat_id": chat_id,
"photo": imagem,
"caption": legenda
},
timeout=60
)

print("Status Telegram:", envio.status_code)
print(envio.text)

if envio.ok:
print("TESTE DE IMAGEM ENVIADO COM SUCESSO!")
else:
print("ERRO AO ENVIAR A IMAGEM.")
