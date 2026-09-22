import os
import requests

url = "https://www.rihappy.com.br/api/catalog_system/pub/products/search?_from=0&_to=0"

r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)

print("STATUS API:", r.status_code)

dados = r.json()

produto = dados[0]

nome = produto["productName"]

imagem = produto["items"][0]["images"][0]["imageUrl"]

link = produto["link"]

preco = produto["items"][0]["sellers"][0]["commertialOffer"]["Price"]

print("PRODUTO:", nome)
print("PRECO:", preco)
print("IMAGEM:", imagem)

token = os.environ["TELEGRAM_BOT_TOKEN"]
chat = os.environ["TELEGRAM_CHAT_ID"]

api = "https://api.telegram.org/bot" + token + "/sendPhoto"

dados_telegram = {"chat_id": chat, "photo": imagem, "caption": "TESTE PANDILLA TOYS\n\n" + nome + "\n\nR$ " + str(preco) + "\n\n" + link}

resultado = requests.post(api, data=dados_telegram, timeout=60)

print("STATUS TELEGRAM:", resultado.status_code)
print(resultado.text)
