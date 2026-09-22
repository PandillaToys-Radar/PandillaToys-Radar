import os
import json
import re
import hashlib
from datetime import datetime, timezone

import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DATABASE_FILE = os.path.join(BASE_DIR, "data", "products.json")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept": "application/json",
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

    texto = str(texto).lower().strip()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def criar_id_produto(nome, url):
    base = normalizar_texto(url)

    if not base:
        base = normalizar_texto(nome)

    return hashlib.sha256(
        base.encode("utf-8")
    ).hexdigest()


def extrair_preco(valor):
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


def detectar_metadados(nome, config):
    texto = normalizar_texto(nome)

    categorias = []
    marcas = []
    personagens = []

    mapa_categorias = {
        "action figures": [
            "action figure",
            "figura de ação",
            "figura articulada",
            "boneco articulado"
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
        ],

        "cards": [
            "card",
            "cards",
            "cartas colecionáveis",
            "tcg"
        ],

        "anime": [
            "anime",
            "manga",
            "mangá",
            "naruto",
            "dragon ball",
            "one piece"
        ],

        "games": [
            "game",
            "gamer",
            "playstation",
            "xbox",
            "nintendo",
            "minecraft"
        ]
    }

    for categoria, palavras in mapa_categorias.items():
        if any(
            palavra in texto
            for palavra in palavras
        ):
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


def buscar_rihappy_api(limite=50):

    url = (
        "https://www.rihappy.com.br/"
        "api/catalog_system/pub/products/search"
    )

    produtos = []

    inicio = 0
    fim = min(limite - 1, 49)

    while len(produtos) < limite:

        params = {
            "_from": inicio,
            "_to": fim
        }

        print(
            f"Consultando API Ri Happy: "
            f"{inicio}-{fim}"
        )

        resposta = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        print(
            f"Status API: {resposta.status_code}"
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if not isinstance(dados, list):
            print("Resposta inesperada da API.")
            break

        if not dados:
            break

        for produto in dados:

            nome = produto.get("productName")
            link = produto.get("link")

            if not nome or not link:
                continue

            if link.startswith("/"):
                link = (
                    "https://www.rihappy.com.br"
                    + link
                )

            preco = None
            imagem = None

            itens = produto.get(
                "items",
                []
            )

            for item in itens:

                # =========================
                # IMAGEM
                # =========================

                imagens = item.get(
                    "images",
                    []
                )

                if imagens and imagem is None:

                    primeira_imagem = imagens[0]

                    imagem = (
                        primeira_imagem.get(
                            "imageUrl"
                        )
                        or primeira_imagem.get(
                            "imageText"
                        )
                    )

                # =========================
                # PREÇO
                # =========================

                sellers = item.get(
                    "sellers",
                    []
                )

                for seller in sellers:

                    oferta = seller.get(
                        "commertialOffer",
                        {}
                    )

                    valor = oferta.get(
                        "Price"
                    )

                    if valor is not None:

                        valor = extrair_preco(
                            valor
                        )

                        if (
                            valor is not None
                            and valor > 0
                        ):
                            preco = valor
                            break

                if preco is not None:
                    break

            if preco is None:
                continue

            produtos.append({
                "nome": nome.strip(),
                "url": link,
                "preco": preco,
                "imagem": imagem,
                "loja": "Ri Happy"
            })

            if len(produtos) >= limite:
                break

        if len(dados) < 50:
            break

        inicio += 50
        fim = inicio + 49

    return produtos


def enviar_telegram_texto(mensagem):

    token = os.environ.get(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.environ.get(
        "TELEGRAM_CHAT_ID"
    )

    if not token or not chat_id:

        print(
            "Telegram não configurado."
        )

        return

    url = (
        f"https://api.telegram.org/"
        f"bot{token}/sendMessage"
    )

    resposta = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": mensagem,
            "disable_web_page_preview": False
        },
        timeout=30
    )

    print(
        f"Telegram texto: "
        f"{resposta.status_code}"
    )

    resposta.raise_for_status()


def enviar_telegram_foto(
    imagem,
    legenda
):

    token = os.environ.get(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.environ.get(
        "TELEGRAM_CHAT_ID"
    )

    if not token or not chat_id:

        print(
            "Telegram não configurado."
        )

        return

    if not imagem:

        print(
            "Produto sem imagem. "
            "Enviando apenas texto."
        )

        enviar_telegram_texto(
            legenda
        )

        return

    url = (
        f"https://api.telegram.org/"
        f"bot{token}/sendPhoto"
    )

    resposta = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "photo": imagem,
            "caption": legenda
        },
        timeout=30
    )

    print(
        f"Telegram foto: "
        f"{resposta.status_code}"
    )

    # Se a imagem falhar, não perdemos o alerta.
    if not resposta.ok:

        print(
            "Falha ao enviar imagem."
        )

        print(
            resposta.text
        )

        enviar_telegram_texto(
            legenda
        )

        return

    resposta.raise_for_status()


def formatar_preco(valor):

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formatar_novo_produto(produto):

    metadados = produto.get(
        "metadados",
        {}
    )

    categorias = ", ".join(
        metadados.get(
            "categorias",
            []
        )
    )

    marcas = ", ".join(
        metadados.get(
            "marcas",
            []
        )
    )

    personagens = ", ".join(
        metadados.get(
            "personagens",
            []
        )
    )

    mensagem = (
        "🆕 NOVO PRODUTO DETECTADO\n\n"
        f"🧸 {produto['nome']}\n\n"
        f"💰 {formatar_preco(produto['preco'])}\n"
    )

    if categorias:

        mensagem += (
            f"🏷️ Categoria: "
            f"{categorias}\n"
        )

    if marcas:

        mensagem += (
            f"🏢 Marca: "
            f"{marcas}\n"
        )

    if personagens:

        mensagem += (
            f"⭐ Personagem: "
            f"{personagens}\n"
        )

    mensagem += (
        f"🛒 {produto['loja']}\n\n"
        f"🔗 {produto['url']}"
    )

    return mensagem


def formatar_queda_preco(
    produto,
    preco_anterior
):

    queda = (
        (
            preco_anterior
            - produto["preco"]
        )
        / preco_anterior
    ) * 100

    return (
        "💰 QUEDA DE PREÇO\n\n"
        f"🧸 {produto['nome']}\n\n"
        f"Antes: "
        f"{formatar_preco(preco_anterior)}\n"
        f"Agora: "
        f"{formatar_preco(produto['preco'])}\n"
        f"📉 -{queda:.1f}%\n\n"
        f"🛒 {produto['loja']}\n"
        f"🔗 {produto['url']}"
    )


def processar_produtos(
    produtos,
    banco,
    config
):

    banco_por_id = {
        produto["id"]: produto
        for produto in banco
    }

    novos = []
    quedas = []

    percentual_minimo = config[
        "monitoramento"
    ][
        "percentual_minimo_queda"
    ]

    for produto in produtos:

        produto["id"] = criar_id_produto(
            produto["nome"],
            produto["url"]
        )

        produto["metadados"] = (
            detectar_metadados(
                produto["nome"],
                config
            )
        )

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        produto[
            "ultima_verificacao"
        ] = agora

        antigo = banco_por_id.get(
            produto["id"]
        )

        if antigo is None:

            produto[
                "primeira_detecao"
            ] = agora

            produto[
                "preco_anterior"
            ] = produto["preco"]

            banco.append(produto)

            banco_por_id[
                produto["id"]
            ] = produto

            novos.append(produto)

            continue

        preco_anterior = antigo.get(
            "preco",
            produto["preco"]
        )

        if (
            produto["preco"]
            < preco_anterior
            and preco_anterior > 0
        ):

            percentual = (
                (
                    preco_anterior
                    - produto["preco"]
                )
                / preco_anterior
            ) * 100

            if percentual >= percentual_minimo:

                quedas.append(
                    (
                        produto,
                        preco_anterior
                    )
                )

        # Atualiza imagem se encontrarmos uma nova.
        if produto.get("imagem"):

            antigo[
                "imagem"
            ] = produto["imagem"]

        antigo[
            "preco_anterior"
        ] = preco_anterior

        antigo[
            "preco"
        ] = produto["preco"]

        antigo[
            "ultima_verificacao"
        ] = agora

        antigo[
            "nome"
        ] = produto["nome"]

        antigo[
            "url"
        ] = produto["url"]

        antigo[
            "metadados"
        ] = produto["metadados"]

    return novos, quedas


def main():

    print(
        "================================"
    )

    print(
        "PANDILLA TOYS RADAR"
    )

    print(
        "================================"
    )

    config = carregar_json(
        CONFIG_FILE,
        {}
    )

    banco = carregar_json(
        DATABASE_FILE,
        []
    )

    limite = config[
        "monitoramento"
    ][
        "max_produtos_por_fonte"
    ]

    produtos = buscar_rihappy_api(
        limite
    )

    print(
        f"Produtos encontrados: "
        f"{len(produtos)}"
    )

    com_imagem = sum(
        1
        for produto in produtos
        if produto.get("imagem")
    )

    print(
        f"Produtos com imagem: "
        f"{com_imagem}"
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

    print(
        f"Novos produtos: "
        f"{len(novos)}"
    )

    print(
        f"Quedas de preço: "
        f"{len(quedas)}"
    )

    if config[
        "monitoramento"
    ][
        "enviar_novos_produtos"
    ]:

        for produto in novos:

            mensagem = (
                formatar_novo_produto(
                    produto
                )
            )

            enviar_telegram_foto(
                produto.get("imagem"),
                mensagem
            )

    if config[
        "monitoramento"
    ][
        "enviar_queda_preco"
    ]:

        for produto, preco_anterior in quedas:

            mensagem = (
                formatar_queda_preco(
                    produto,
                    preco_anterior
                )
            )

            enviar_telegram_foto(
                produto.get("imagem"),
                mensagem
            )

    print(
        "Radar finalizado."
    )


if __name__ == "__main__":
    main()
