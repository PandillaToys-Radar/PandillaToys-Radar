import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": "🤖 Pandilla Toys Radar online!\n\n🚀 Primeiro teste realizado com sucesso."
    },
)

response.raise_for_status()

print("Mensagem enviada com sucesso!")
