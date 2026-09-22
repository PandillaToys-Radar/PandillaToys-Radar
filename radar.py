import os
import requests

API = "https://www.rihappy.com.br/api/catalog_system/pub/products/search"

HEADERS = {
"User-Agent": "Mozilla/5.0",
"Accept": "application/json"
}

resposta = requests.get(
API,
params={"_from": 0, "_to": 0},
headers=HEADERS,
timeout=30
)

print("STATUS API:", resposta.status_code)

dados = resposta.json()

produto = dados[0]

nome = produto.get("productName", "Produto sem nome")
link = produto.get("link", "")
imagem = None
preco = None

itens = produto.get("items", [])

for item in itens:
imagens = item.get("images", [])

if imagens:
    imagem = imagens[0].get("imageUrl")

sellers = item.get("sellers", [])

for seller in sellers:
    oferta = seller.get("commertialOffer", {})
    valor = oferta.get("Price")

    if valor:
        preco = valor
        break

if preco:
    break

if link.startswith("/"):
link = "https://www.rihappy.com.br" + link

print("PRODUTO:", nome)
print("PRECO:", preco)
print("IMAGEM ENCONTRADA:", bool(imagem))
print("IMAGEM:", imagem)

token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

print("TOKEN ENCONTRADO:", bool(token))
print("CHAT ID ENCONTRADO:", bool(chat_id))

telegram_url = "https://api.telegram.org/bot" + token + "/sendPhoto"

legenda = "TESTE DE IMAGEM - PANDILLA TOYS RADAR\n\n" + nome + "\n\nPreco: R$ " + str(preco) + "\n\n" + link

resposta_telegram = requests.post(
telegram_url,
data={
"chat_id": chat_id,
"photo": imagem,
"caption": legenda
},
timeout=60
)

print("STATUS TELEGRAM:", resposta_telegram.status_code)
print(resposta_telegram.text)

print("TESTE FINALIZADO.")
