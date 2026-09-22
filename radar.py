import os
import json
import re
import requests

BASE_DIR = os.path.dirname(os.path.abspath(**file**))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

HEADERS = {
"User-Agent": (
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
"AppleWebKit/537.36 (KHTML, like Gecko) "
"Chrome/139.0 Safari/537.36"
),
"Accept": "application/json",
"Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
}

def extrair_preco(valor):

```
if valor is None:
    return None

if isinstance(valor, (int, float)):
    return float(valor)

texto = str(valor)
texto = texto.replace("R$", "").strip()

if "," in texto:
    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")

try:
    return float(texto)
except ValueError:
    return None
```

def buscar_produto_teste():

```
url = (
    "https://www.rihappy.com.br/"
    "api/catalog_system/pub/products/search"
)

params = {
    "_from": 0,
    "_to": 0
}

print("Consultando primeiro produto da Ri Happy...")

resposta = requests.get(
    url,
    params=params,
    headers=HEADERS,
    timeout=30
)

print(f"Status API: {resposta.status_code}")

resposta.raise_for_status()

dados = resposta.json()

if not dados:
    print("Nenhum produto encontrado.")
    return None

produto = dados[0]

nome = produto.get("productName")
link = produto.get("link")

if link and link.startswith("/"):
    link = (
        "https://www.rihappy.com.br"
        + link
    )

preco = None
imagem = None

for item in produto.get("items", []):

    imagens = item.get("images", [])

    if imagens and imagem is None:

        primeira_imagem = imagens[0]

        imagem = (
            primeira_imagem.get("imageUrl")
            or primeira_imagem.get("imageText")
        )

    for seller in item.get("sellers", []):

        oferta = seller.get(
            "commertialOffer",
            {}
        )

        valor = oferta.get("Price")

        if valor is not None:

            valor = extrair_preco(valor)

            if valor is not None and valor > 0:
                preco = valor
                break

    if preco is not None:
        break

return {
    "nome": nome,
    "url": link,
    "preco": preco,
    "imagem": imagem
}
```

def formatar_preco(valor):

```
if valor is None:
    return "Preço não informado"

return (
    f"R$ {valor:,.2f}"
    .replace(",", "X")
    .replace(".", ",")
    .replace("X", ".")
)
```

def enviar_foto(produto):

```
token = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)

chat_id = os.environ.get(
    "TELEGRAM_CHAT_ID"
)

if not token or not chat_id:

    print("Telegram não configurado.")
    return

imagem = produto.get("imagem")

if not imagem:

    print("❌ Produto não possui imagem.")
    return

legenda = (
    "🧪 TESTE DE IMAGEM — PANDILLA TOYS RADAR\n\n"
    f"🧸 {produto['nome']}\n\n"
    f"💰 {formatar_preco(produto['preco'])}\n\n"
    f"🛒 Ri Happy\n\n"
    f"🔗 {produto['url']}"
)

url = (
    f"https://api.telegram.org/"
    f"bot{token}/sendPhoto"
)

print("Enviando imagem para o Telegram...")
print(f"Imagem: {imagem}")

resposta = requests.post(
    url,
    data={
        "chat_id": chat_id,
        "photo": imagem,
        "caption": legenda
    },
    timeout=60
)

print(
    f"Resposta Telegram: "
    f"{resposta.status_code}"
)

print(resposta.text)

resposta.raise_for_status()
```

def main():

```
print("================================")
print("PANDILLA TOYS RADAR")
print("TESTE DE IMAGEM")
print("================================")

produto = buscar_produto_teste()

if produto is None:
    return

print()
print(f"Produto: {produto['nome']}")
print(f"Preço: {produto['preco']}")
print(f"Imagem encontrada: {bool(produto['imagem'])}")

if produto["imagem"]:
    enviar_foto(produto)
    print()
    print("✅ TESTE FINALIZADO.")
else:
    print()
    print("❌ Não foi encontrada imagem.")
```

if **name** == "**main**":
main()
