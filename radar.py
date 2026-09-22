import os
import json
import re
import hashlib
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DATABASE_FILE = os.path.join(BASE_DIR, "data", "products.json")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
}


def carregar_json(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


def normalizar_texto(texto):
    if not texto:
        return ""

    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def criar_id_produto(nome, url):
    """
    Cria um identificador estável para o produto.

    Primeiro usamos a URL.
    Se a loja mudar pequenos detalhes do nome,
    o produto continua sendo identificado pela URL.
    """

    base = normalizar_texto(url)

    if not base:
        base = normalizar_texto(nome)

    return hashlib.sha256(
        base.encode("utf-8")
    ).hexdigest()


def extrair_preco(texto):
    """
    Converte:
    R$ 299,99 -> 299.99
    """

    if not texto:
        return None

    padrao = r"R\$\s*([\d\.]+,\d{2})"

    encontrados = re.findall(padrao, texto)

    if not encontrados:
        return None

    valor = encontrados[-1]

    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return None


def detectar_metadados(nome, config):
    texto = normalizar_texto(nome)

    categorias = []
    marcas = []
    personagens = []

    mapa_categorias = {
        "action figures": [
            "action figure",
            "figura de ação",
            "figura articulada"
        ],
        "estatuetas": [
            "estátua",
            "estatua",
            "estatueta",
            "statue"
        ],
        "carrinhos": [
            "carrinho",
            "carro",
            "hot wheels",
            "matchbox"
        ],
        "lego": [
            "lego"
        ],
        "pelucias": [
            "pelúcia",
            "pelucia",
            "plush"
        ],
        "funko": [
            "funko",
            "pop!"
        ],
        "miniaturas": [
            "miniatura",
            "miniaturas"
        ],
        "puzzles": [
            "quebra-cabeça",
            "quebra cabeça",
            "puzzle"
        ],
        "board games": [
            "jogo de tabuleiro",
            "board game"
        ]
    }

    for categoria, palavras in mapa_categorias.items():
        if any(palavra in texto for palavra in palavras):
            categorias.append(categoria)

    for marca in config["filtros"]["marcas"]:
        if normalizar_texto(marca) in texto:
            marcas.append(marca)

    for personagem in config["filtros"]["personagens"]:
        if normalizar_texto(personagem) in texto:
            personagens.append(personagem)

    return {
        "categorias": categorias,
        "marcas": marcas,
        "personagens": personagens
    }


def baixar_pagina(url):
    print(f"Baixando: {url}")

    resposta = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    resposta.raise_for_status()

    return resposta.text


def extrair_produtos_rihappy(html, limite=50):
    """
    Extrator inicial da Ri Happy.

    A página pública da categoria apresenta os produtos
    com nome, preço e links.
    """

    soup = BeautifulSoup(html, "lxml")

    produtos = []
    urls_vistas = set()

    for link in soup.find_all("a", href=True):

        href = link.get("href", "").strip()

        if not href:
            continue

        if "/p/" not in href:
            continue

        if href.startswith("/"):
            href = "https://www.rihappy.com.br" + href

        if href in urls_vistas:
            continue

        nome = link.get_text(" ", strip=True)

        if not nome or len(nome) < 5:
            continue

        container = link

        texto_container = ""

        for _ in range(4):
            if container.parent:
                container = container.parent
                texto_container = container.get_text(
                    " ",
                    strip=True
                )

                if "R$" in texto_container:
                    break

        preco = extrair_preco(texto_container)

        if preco is None:
            continue

        produtos.append({
            "nome": nome,
            "url": href,
            "preco": preco,
            "loja": "Ri Happy"
        })

        urls_vistas.add(href)

        if len(produtos) >= limite:
            break

    return produtos


def enviar_telegram(mensagem):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram não configurado.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    resposta = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": mensagem,
            "disable_web_page_preview": False
        },
        timeout=30
    )

    resposta.raise_for_status()


def formatar_novo_produto(produto):
    metadados = produto.get("metadados", {})

    categorias = ", ".join(
        metadados.get("categorias", [])
    )

    marcas = ", ".join(
        metadados.get("marcas", [])
    )

    personagens = ", ".join(
        metadados.get("personagens", [])
    )

    mensagem = (
        "🆕 NOVO PRODUTO DETECTADO\n\n"
        f"🧸 {produto['nome']}\n\n"
        f"💰 R$ {produto['preco']:.2f}".replace(".", ",")
        + "\n"
    )

    if categorias:
        mensagem += f"🏷️ Categoria: {categorias}\n"

    if marcas:
        mensagem += f"🏢 Marca: {marcas}\n"

    if personagens:
        mensagem += f"⭐ Personagem: {personagens}\n"

    mensagem += (
        f"🛒 {produto['loja']}\n\n"
        f"🔗 {produto['url']}"
    )

    return mensagem


def formatar_queda_preco(produto, preco_anterior):
    queda = ((preco_anterior - produto["preco"]) / preco_anterior) * 100

    return (
        "💰 QUEDA DE PREÇO\n\n"
        f"🧸 {produto['nome']}\n\n"
        f"~~ R$ {preco_anterior:.2f} ~~\n"
        f"🔥 R$ {produto['preco']:.2f}\n"
        f"📉 -{queda:.1f}%\n\n"
        f"🛒 {produto['loja']}\n"
        f"🔗 {produto['url']}"
    ).replace(".", ",")


def processar_produtos(produtos, banco, config):
    banco_por_id = {
        produto["id"]: produto
        for produto in banco
    }

    novos = []
    quedas = []

    percentual_minimo = config[
        "monitoramento"
    ]["percentual_minimo_queda"]

    for produto in produtos:

        produto["id"] = criar_id_produto(
            produto["nome"],
            produto["url"]
        )

        produto["metadados"] = detectar_metadados(
            produto["nome"],
            config
        )

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        produto["ultima_verificacao"] = agora

        antigo = banco_por_id.get(
            produto["id"]
        )

        if antigo is None:

            produto["primeira_detecao"] = agora
            produto["preco_anterior"] = produto["preco"]

            banco.append(produto)
            banco_por_id[produto["id"]] = produto

            novos.append(produto)

            continue

        preco_anterior = antigo.get(
            "preco",
            produto["preco"]
        )

        if (
            produto["preco"] < preco_anterior
            and preco_anterior > 0
        ):

            percentual = (
                (preco_anterior - produto["preco"])
                / preco_anterior
            ) * 100

            if percentual >= percentual_minimo:
                quedas.append(
                    (produto, preco_anterior)
                )

        antigo["preco_anterior"] = preco_anterior
        antigo["preco"] = produto["preco"]
        antigo["ultima_verificacao"] = agora
        antigo["nome"] = produto["nome"]
        antigo["url"] = produto["url"]
        antigo["metadados"] = produto["metadados"]

    return novos, quedas


def main():

    print("================================")
    print("PANDILLA TOYS RADAR")
    print("================================")

    config = carregar_json(
        CONFIG_FILE,
        {}
    )

    banco = carregar_json(
        DATABASE_FILE,
        []
    )

    fonte = config["fontes"][0]

    if not fonte["ativa"]:
        print("Fonte desativada.")
        return

    html = baixar_pagina(
        fonte["url"]
    )

    produtos = extrair_produtos_rihappy(
        html,
        config["monitoramento"][
            "max_produtos_por_fonte"
        ]
    )

    print(
        f"Produtos encontrados: {len(produtos)}"
    )

    novos, quedas = processar_produtos(
        produtos,
        banco,
        config
    )

    salvar_json(
        DATABASE_FILE,
        banco
    )

    print(f"Novos produtos: {len(novos)}")
    print(f"Quedas de preço: {len(quedas)}")

    if config["monitoramento"][
        "enviar_novos_produtos"
    ]:

        for produto in novos:

            mensagem = formatar_novo_produto(
                produto
            )

            enviar_telegram(
                mensagem
            )

    if config["monitoramento"][
        "enviar_queda_preco"
    ]:

        for produto, preco_anterior in quedas:

            mensagem = formatar_queda_preco(
                produto,
                preco_anterior
            )

            enviar_telegram(
                mensagem
            )

    print("Radar finalizado.")


if __name__ == "__main__":
    main()
